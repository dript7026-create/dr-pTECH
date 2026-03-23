#include <gb/gb.h>
#include <gb/drawing.h>
#include <gb/font.h>

// Tile graphics data for TOMMY GOOMBA
const unsigned char tileset[] = {
    // Define your tile graphics here
    // Each tile is 8x8 pixels, represented in a byte array
    // Example tile data (replace with actual graphics)
    0xFF, 0x81, 0x81, 0xFF, // Tile 1
    0xFF, 0xA5, 0xA5, 0xFF, // Tile 2
    // Add more tiles as needed
};

// Function to load the tileset into VRAM
void load_tileset() {
    set_sprite_data(0, sizeof(tileset) / 8, tileset);
}