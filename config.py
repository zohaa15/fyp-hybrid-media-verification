import os

# Paths to external tools.
# Override by setting these as environment variables, or edit the defaults below
# to match the install paths on your machine.
TMK_HASH_EXE = os.environ.get(
    "TMK_HASH_EXE",
    r"C:\Users\zohaa\facebook-example\ThreatExchange\tmk\cpp\tmk-hash-video.exe"
)

TMK_QUERY_EXE = os.environ.get(
    "TMK_QUERY_EXE",
    r"C:\Users\zohaa\facebook-example\ThreatExchange\tmk\cpp\tmk-query.exe"
)

FFMPEG_EXE = os.environ.get(
    "FFMPEG_EXE",
    r"C:\Users\zohaa\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
)
