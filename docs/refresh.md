# AuthRefreshToken
Knox provides an option to [enable](settings.md#enable_refresh_token) refresh tokens which can be used as proof of ownership when your auth `token` expires.   

When enabled `knox.LoginView` issues a `refresh_token` along with the regular auth `token`, whenever your auth `token` expires,
that `refresh_token` can later be used to have a new valid auth `token` issued to you by the `knox.views.RefreshTokenView`.
Tokens are rotated and kept track of, whenever an old `refresh_token` is used in an attempt to get a new auth `token`, the whole family of that `refresh_token` is invalidated.
The tracking is done by `knox.RefreshFamily` model where each `refresh_token` issued by `knox.LoginView` is a parent of the subseuent 
`token` and `refresh_token` pairs issued by `knox.RefreshTokenView`.



