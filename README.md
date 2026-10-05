# media-player
This set of programs is designed to run the VR/AR@MIT matrix screen with member submitted content.

To set it up, copy `bot/.env.example` to `bot/.env`, fill it in, and run `bot/main.py`.

```idk
        4
     _________
    |         |
 3  |         |
    |_________|
```
(in pixels):
```idk
        256
     _________
    |         |
192 |         |
    |_________|
```

Theoretically, with modification it should work on any size but some animations/placements will be off.


The overall idea of this project is to provide a discord interface for club members to upload
a video to the library and configure / queue whats playing,
in addition to a set of scrolling text at the bottom of the matrix which they can also
submit.
