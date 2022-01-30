# spotifyslackstatus

> I just wanted my currently playing song from Spotify to show up in my Slack status.

## Functionality
- [x] Can OAuth with Spotify
- [x] Can OAuth with Slack
- [x] Can read Spotify user's profle
- [x] Can read Spotify user's currently playing track
- [x] Can read Slack user's profile
- [x] Can read Slack user's status emoji and text
- [x] Can write Slack user's status emoji and text
- [x] Can save Slack user's original status emoji and text
- [x] Can restore Slack user's original status emoji and text

## TODO
- [ ] Convert Flask-Session to use Redis / Memcached / MongoDB instead of filesystem
- [ ] Convert Flask app to AWS Serverless app (static website + API Gateway + Lambda + session storage)
- [ ] Mechanism to detect when song changed (preferably event driven instead of polling Spotify API)
