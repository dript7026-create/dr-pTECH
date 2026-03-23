CC = gbcc
CFLAGS = -mgb -O2
OBJ = src/main.o src/game.o src/state.o src/player.o src/actors.o src/combat.o src/world_map.o src/stage_manager.o src/save_system.o src/intro_scene.o src/ending_scene.o src/assets/tiles/tileset.o src/assets/maps/world_map.o src/assets/maps/stage_maps.o src/assets/sprites/sprites.o src/stages/stage_01.o src/stages/stage_02.o src/stages/stage_03.o src/stages/stage_04.o src/stages/stage_05.o src/stages/stage_06.o src/stages/stage_07.o src/stages/stage_08.o src/stages/stage_09.o src/stages/stage_10.o src/stages/stage_11.o src/stages/stage_12.o src/stages/stage_13.o src/stages/stage_14.o src/stages/stage_15.o src/stages/stage_16.o src/stages/stage_17.o src/stages/stage_18.o src/stages/stage_19.o src/stages/stage_20.o src/stages/stage_21.o src/stages/stage_22.o src/stages/stage_23.o src/stages/stage_24.o src/stages/stage_25.o src/stages/stage_26.o src/stages/stage_27.o src/stages/stage_28.o src/stages/stage_29.o src/stages/stage_30.o src/stages/stage_31.o src/stages/stage_32.o src/stages/stage_33.o src/stages/stage_34.o src/stages/stage_35.o src/stages/stage_36.o src/stages/stage_37.o src/stages/stage_38.o src/stages/stage_39.o src/stages/stage_40.o src/stages/stage_41.o src/stages/stage_42.o src/stages/stage_43.o src/stages/stage_44.o src/stages/stage_45.o src/stages/stage_46.o src/stages/stage_47.o src/stages/stage_48.o src/stages/stage_49.o src/stages/stage_50.o src/stages/stage_51.o src/stages/stage_52.o src/stages/stage_53.o src/stages/stage_54.o src/stages/stage_55.o src/stages/stage_56.o src/stages/stage_57.o src/stages/stage_58.o src/stages/stage_59.o src/stages/stage_60.o src/stages/stage_61.o src/stages/stage_62.o src/stages/stage_63.o src/stages/stage_64.o src/stages/stage_65.o src/stages/stage_66.o

all: tommygoomba.gb

tommygoomba.gb: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f src/*.o tommygoomba.gb

.PHONY: all clean