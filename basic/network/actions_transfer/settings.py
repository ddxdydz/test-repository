from basic.network.actions_transfer.Action import Action

XY_ACTIONS = (
    Action.ON_MOVE,
    Action.ON_CLICK_RELEASED_LEFT,
    Action.ON_CLICK_RELEASED_RIGHT,
    Action.ON_CLICK_PRESSED_LEFT,
    Action.ON_CLICK_PRESSED_RIGHT,
)

SCROLL_ADDITIONAL_VALUE = 1024

STOP_COMMAND = (Action.ON_PRESS_SPECIAL, 163, 2)
