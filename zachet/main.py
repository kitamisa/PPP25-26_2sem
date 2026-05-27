def show_menu():
    print("=" * 50)
    print("            ЛАБИРИНТ")
    print("=" * 50)
    print("\nКоманды:")
    print("  w - движение вверх")
    print("  a - движение влево")
    print("  s - движение вниз")
    print("  d - движение вправо")
    print("  restart - начать заново")
    print("  exit - выход")
    print("=" * 50)


def create_maze():
    maze = [
        ["#", "#", "#", "#", "#", "#", "#", "#", "#", "#"],
        ["#", "S", " ", " ", "#", " ", " ", " ", " ", "#"],
        ["#", "#", "#", " ", "#", " ", "#", "#", " ", "#"],
        ["#", " ", " ", " ", " ", " ", "#", " ", " ", "#"],
        ["#", " ", "#", "#", "#", "#", "#", " ", "#", "#"],
        ["#", " ", " ", " ", "#", " ", " ", " ", " ", "#"],
        ["#", "#", "#", " ", "#", " ", "#", "#", " ", "#"],
        ["#", " ", " ", " ", " ", " ", "#", " ", " ", "#"],
        ["#", " ", "#", "#", "#", "#", "#", " ", "E", "#"],
        ["#", "#", "#", "#", "#", "#", "#", "#", "#", "#"]
    ]
    return maze


def find_start(maze):
    for i in range(len(maze)):
        for j in range(len(maze[i])):
            if maze[i][j] == "S":
                return i, j
    return 1, 1


def print_maze(maze, player_row, player_col):
    print("\n" + "-" * 50)
    print("ТЕКУЩАЯ КАРТА:")
    print("-" * 50)

    for i in range(len(maze)):
        row_str = ""
        for j in range(len(maze[i])):
            if i == player_row and j == player_col:
                row_str += " P "
            elif maze[i][j] == "#":
                row_str += "███"
            elif maze[i][j] == "S":
                row_str += " S "
            elif maze[i][j] == "E":
                row_str += " E "
            else:
                row_str += "   "
        print(row_str)

    print("-" * 50)
    print("S - старт, E - выход, P - игрок, ███ - стена")
    print("-" * 50)


def get_command():
    while True:
        command = input("\n> ").strip().lower()
        if command in ["w", "a", "s", "d", "restart", "exit"]:
            return command
        print("Ошибка! Используйте w, a, s, d, restart или exit")


def move_player(maze, player_row, player_col, direction):
    new_row, new_col = player_row, player_col

    if direction == "w":
        new_row -= 1
    elif direction == "s":
        new_row += 1
    elif direction == "a":
        new_col -= 1
    elif direction == "d":
        new_col += 1

    if new_row < 0 or new_row >= len(maze) or new_col < 0 or new_col >= len(maze[0]):
        print("Ошибка! Нельзя выйти за пределы лабиринта")
        return player_row, player_col, False

    if maze[new_row][new_col] == "#":
        print("Ошибка! Там стена, прохода нет")
        return player_row, player_col, False

    if maze[new_row][new_col] == "E":
        print("\n*** ПОЗДРАВЛЯЮ! ВЫ НАШЛИ ВЫХОД! ***")
        return new_row, new_col, True

    return new_row, new_col, False


def play_maze():
    maze = create_maze()
    player_row, player_col = find_start(maze)
    game_won = False

    print("\n" + "=" * 50)
    print("         НАЧАЛО ИГРЫ!")
    print("Найдите выход (E), двигаясь по лабиринту")
    print("=" * 50)

    while not game_won:
        print_maze(maze, player_row, player_col)

        command = get_command()

        if command == "restart":
            print("\n" + "=" * 50)
            print("         ИГРА ПЕРЕЗАПУЩЕНА")
            print("=" * 50)
            return "restart"

        if command == "exit":
            print("\nСпасибо за игру! До свидания!")
            return "exit"

        player_row, player_col, game_won = move_player(maze, player_row, player_col, command)

    print_maze(maze, player_row, player_col)
    return "finished"


def main():
    show_menu()

    while True:
        print("\nВведите restart чтобы начать игру или exit для выхода")
        start_command = get_command()

        if start_command == "exit":
            print("\nСпасибо за игру! До свидания!")
            return
        elif start_command != "restart":
            print("Ошибка! Введите restart или exit")
            continue

        result = play_maze()

        if result == "exit":
            return
        elif result == "finished":
            print("\n" + "=" * 50)
            print("Хотите сыграть еще?")
            print("restart - начать заново")
            print("exit - выход")

            while True:
                cmd = get_command()
                if cmd == "restart":
                    break
                elif cmd == "exit":
                    print("\nСпасибо за игру! До свидания!")
                    return
                else:
                    print("Ошибка! Введите restart или exit")


if __name__ == "__main__":
    main()

