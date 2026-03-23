{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "CMake Build",
      "type": "shell",
      "command": "cmake -S . -B build && cmake --build build",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Make Build",
      "type": "shell",
      "command": "make",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "GCC Build",
      "type": "shell",
      "command": "gcc -O2 -Wall -o {project_name} src/*.c",
      "group": "build",
      "problemMatcher": []
    }
  ]
}
