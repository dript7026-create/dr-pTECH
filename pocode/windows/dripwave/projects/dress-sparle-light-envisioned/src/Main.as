package {
    import flash.display.Sprite;
    import flash.display.StageAlign;
    import flash.display.StageScaleMode;
    import flash.events.Event;

    [SWF(width="960", height="540", frameRate="60", backgroundColor="#060A12")]
    public class Main extends Sprite {
        private var script:GameScript;

        public function Main() {
            if (stage) {
                initialize();
            } else {
                addEventListener(Event.ADDED_TO_STAGE, onAddedToStage);
            }
        }

        private function onAddedToStage(event:Event):void {
            removeEventListener(Event.ADDED_TO_STAGE, onAddedToStage);
            initialize();
        }

        private function initialize():void {
            stage.align = StageAlign.TOP_LEFT;
            stage.scaleMode = StageScaleMode.NO_SCALE;
            stage.frameRate = 60;

            script = new GameScript("Dress SparLE: Light Envisioned");
            addChild(script);
            addEventListener(Event.ENTER_FRAME, onFrame);
        }

        private function onFrame(event:Event):void {
            script.update();
        }
    }
}
