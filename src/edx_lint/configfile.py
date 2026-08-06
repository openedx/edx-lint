"""Config file tools for edx_lint."""


def merge_configs(main, tweaks):
    """Merge tweaks into a main config file."""
    for section in tweaks.sections():
        for option in tweaks.options(section):
            value = tweaks.get(section, option)
            if option.endswith("+"):
                option = option[:-1]
                value = main.get(section, option) + value
            main.set(section, option, value)
