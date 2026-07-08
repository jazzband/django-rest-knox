from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.signals import token_expired

User = get_user_model()


class CleanupTokenTestCase(TestCase):
    """
    Characterization tests for ``TokenAuthentication._cleanup_token``.

    These lock in the current behaviour so that the planned bulk-delete
    optimisation can be verified against the same contract.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='john.doe', email='john@example.com', password='hunter2',
        )
        self.user2 = User.objects.create_user(
            username='jane.doe', email='jane@example.com', password='hunter2',
        )
        self.factory = APIRequestFactory()

    def _authenticate(self, token):
        request = self.factory.get('/')
        request.META = {'HTTP_AUTHORIZATION': f'Token {token}'}
        return TokenAuthentication().authenticate(request)

    # -- deletion scoping ------------------------------------------------

    def test_cleanup_deletes_expired_tokens_for_same_user(self):
        """
        Authenticating with a valid token deletes the same user's expired
        tokens but leaves the valid one intact.
        """
        _, valid_token = AuthToken.objects.create(user=self.user)
        AuthToken.objects.create(user=self.user, expiry=timedelta(seconds=-1))
        AuthToken.objects.create(user=self.user, expiry=timedelta(seconds=-1))

        self.assertEqual(AuthToken.objects.filter(user=self.user).count(), 3)
        self._authenticate(valid_token)
        self.assertEqual(AuthToken.objects.filter(user=self.user).count(), 1)
        self.assertTrue(
            AuthToken.objects.filter(user=self.user).exists(),
        )

    def test_cleanup_does_not_delete_other_users_expired_tokens(self):
        """
        Expired tokens belonging to a *different* user must survive cleanup
        triggered by authenticating an unrelated user's token.
        """
        _, valid_token = AuthToken.objects.create(user=self.user)
        AuthToken.objects.create(user=self.user2, expiry=timedelta(seconds=-1))

        self.assertEqual(AuthToken.objects.filter(user=self.user2).count(), 1)
        self._authenticate(valid_token)
        self.assertEqual(AuthToken.objects.filter(user=self.user2).count(), 1)

    def test_cleanup_does_not_delete_tokens_with_null_expiry(self):
        """
        Tokens with ``expiry=None`` (no expiration) must never be removed by
        cleanup.
        """
        _, valid_token = AuthToken.objects.create(user=self.user)
        AuthToken.objects.create(user=self.user, expiry=None)

        self._authenticate(valid_token)
        self.assertEqual(
            AuthToken.objects.filter(user=self.user, expiry__isnull=True).count(),
            1,
        )

    def test_cleanup_deletes_expired_auth_token_and_skips_it(self):
        """
        Authenticating with an already-expired token deletes it and raises
        AuthenticationFailed (the token is skipped).
        """
        from rest_framework.exceptions import AuthenticationFailed

        _, expired_token = AuthToken.objects.create(
            user=self.user, expiry=timedelta(seconds=-1),
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        with self.assertRaises(AuthenticationFailed):
            self._authenticate(expired_token)
        self.assertEqual(AuthToken.objects.count(), 0)

    # -- signals ---------------------------------------------------------

    def test_cleanup_signal_source_other_token(self):
        """
        When an expired *sibling* token is cleaned up during authentication,
        the ``token_expired`` signal fires with ``source="other_token"``.
        """
        _, valid_token = AuthToken.objects.create(user=self.user)
        AuthToken.objects.create(user=self.user, expiry=timedelta(seconds=-1))

        received = []

        def handler(sender, username, source, **kwargs):
            received.append(source)

        token_expired.connect(handler)
        try:
            self._authenticate(valid_token)
        finally:
            token_expired.disconnect(handler)

        self.assertIn('other_token', received)

    def test_cleanup_signal_source_auth_token(self):
        """
        When the token being authenticated is itself expired, the
        ``token_expired`` signal fires with ``source="auth_token"``.
        """
        from rest_framework.exceptions import AuthenticationFailed

        _, expired_token = AuthToken.objects.create(
            user=self.user, expiry=timedelta(seconds=-1),
        )

        received = []

        def handler(sender, username, source, **kwargs):
            received.append(source)

        token_expired.connect(handler)
        try:
            with self.assertRaises(AuthenticationFailed):
                self._authenticate(expired_token)
        finally:
            token_expired.disconnect(handler)

        self.assertIn('auth_token', received)

    # -- query-count baseline -------------------------------------------

    def test_cleanup_query_count_with_expired_siblings(self):
        """
        Baseline query count when cleanup deletes expired siblings.

        Currently this is ``2 + N`` where N is the number of expired tokens
        (1 filter + 1 ``auth_token_set.all()`` + N per-token deletes).  This
        test documents the N+1 behaviour so the optimisation can be verified.
        """
        _, valid_token = AuthToken.objects.create(user=self.user)
        for _ in range(5):
            AuthToken.objects.create(user=self.user, expiry=timedelta(seconds=-1))

        request = self.factory.get('/')
        request.META = {'HTTP_AUTHORIZATION': f'Token {valid_token}'}
        # 1 filter + 1 auth_token_set.all() + 5 deletes = 7
        with self.assertNumQueries(7):
            TokenAuthentication().authenticate(request)
