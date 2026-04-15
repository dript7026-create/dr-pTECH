import argparse
import sys

from .gui import run_app as run_gui_app
from .live_render import run_live_render
from .playback import run_app as run_playback_app


def main(argv=None):
    parser = argparse.ArgumentParser(description="Launch the DirkOdds desktop application.")
    parser.add_argument("--playback-report", help="Open the Qt playback window for a DirkOdds report JSON")
    parser.add_argument("--live-render-report", help="Open the Panda3D live-render window for a DirkOdds report JSON")
    parser.add_argument("--fixture-index", type=int, default=0, help="Simulation index inside the report")
    parser.add_argument("--offscreen", action="store_true", help="Create the live renderer in offscreen mode")
    parser.add_argument("--auto-close-after", type=float, help="Auto-close the live renderer after N wall-clock seconds")
    parser.add_argument("--software-render", action="store_true", help="Force Panda3D software rendering when hardware OpenGL is unavailable")
    args = parser.parse_args(argv)

    if args.playback_report and args.live_render_report:
        parser.error("Choose either --playback-report or --live-render-report, not both.")

    if args.playback_report:
        run_playback_app(args.playback_report)
        return

    if args.live_render_report:
        run_live_render(
            args.live_render_report,
            fixture_index=args.fixture_index,
            offscreen=args.offscreen,
            auto_close_after=args.auto_close_after,
            software_render=args.software_render,
        )
        return

    run_gui_app()


if __name__ == "__main__":
    main(sys.argv[1:])
