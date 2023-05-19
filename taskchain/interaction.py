from __future__ import annotations

def input_bool(text: str):
    from colorama import Fore
    _text = "\n\n" + Fore.CYAN + text + "enter Y/N: \n>>>>>>"
    print(_text + Fore.RESET)
    response = input()
    response.lower()
    if response in ["y", "yes", "true", "1"]:
        return True
    elif response in ["n", "no", "false", "0"]:
        return False
    else:
        print("ERROR: invalid input please only enter Y/N")
        return input_bool(text)


def input_bool_message(text: str, return_on_true="approved", return_on_false="refused"):
    if input_bool(text):
        return return_on_true
    return return_on_false


def input_feedback(text: str, stop_command="stop"):
    from colorama import Fore
    _text = "\n\n" + Fore.CYAN + text + "enter your feedback or enter stop to cancel: \n>>>>>>"
    print(_text + Fore.RESET)
    response = input()
    response = "" if response is None else response
    print(Fore.GREEN, "feedback received:", Fore.RESET, response)
    return response


def select_option(options: list[any], prefix: str = None, suffix: str = None) -> any:
    from colorama import Fore
    if prefix is None:
        prefix = ""
    _options = "\n - ".join([f".{n+1}. {sel}" for n, sel in enumerate(options)])
    print(Fore.YELLOW + "\n - "+ _options + Fore.RESET)
    _cta_options = " ".join([f"<{n+1}>" for n, sel in enumerate(options)])
    cta = f"\n\nPlease select one of the options above by entering the number of the option: \n{_options}.\n>>>>>>"
    if suffix is None:
        suffix = ""
    console_msg = Fore.BLUE + prefix + cta + suffix + Fore.RESET
    print(console_msg)
    choice = None
    while choice is None:
        selected = input()
        try:
            selected = int(selected)
            choice = options[selected-1]
        except ValueError:
            print(f"wrong input: {selected}. Please enter only a number from: {_options}.")
    return choice


def select_option_cta_only(options: list[int]) -> int:
    from colorama import Fore
    _options = " ".join([f"<{n+1}>" for n in options])
    suffix = f"\n\nPlease select one of the options above by entering the number of the option: {_options}.\n>>>>>>"
    print(Fore.BLUE + suffix)
    while True:
        selected = input()
        try:
            if int(selected)-1 in options:
                return int(selected)-1
        except ValueError:
            print(f"wrong input: {selected}. Please enter only a number from: {_options}.")