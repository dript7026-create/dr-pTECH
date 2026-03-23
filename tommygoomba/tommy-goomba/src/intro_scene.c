#include <gb/gb.h>
#include <stdio.h>
#include "game.h"
#include "state.h"

void intro_scene() {
    // Display introductory narrative
    printf("Welcome to TOMMY GOOMBA!\n");
    printf("An original story by the Carell brothers.\n");
    printf("The story starts in the house in the Mushroom Kingdom...\n");
    
    // Simulate the scene where Tommy's family is introduced
    printf("You see Tommy and his wife and children...\n");
    delay(2000); // Wait for 2 seconds

    // Introduce the strange figures
    printf("Suddenly, a strange figure and his brother show up...\n");
    delay(2000); // Wait for 2 seconds

    // Describe the chaos
    printf("They jump down with fierce force onto the house...\n");
    printf("Crushing Tommy's children!\n");
    delay(2000); // Wait for 2 seconds

    // The wife is taken away
    printf("Next, they snag the wife and run off...\n");
    printf("Leaving behind nothing but their cousins laughing on Facetime...\n");
    delay(2000); // Wait for 2 seconds

    // Tommy's reaction
    printf("Tommy cries for roughly 3 minutes...\n");
    printf("As the house floods with tears in real-time...\n");
    delay(3000); // Simulate 3 minutes of crying (for demo purposes, we use a shorter delay)

    // The iPhone shorts out
    printf("The iPhone shorts in Tommy's tears...\n");
    printf("Shocking Tommy awake with electrically charged speed abilities!\n");
    delay(2000); // Wait for 2 seconds

    // Transition to the first stage
    printf("Tommy charges off into the first stage...\n");
    // Here you would typically call the function to load the first stage
    // load_stage(1);
}