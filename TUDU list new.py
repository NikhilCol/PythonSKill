import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import calendar as cal_module
import json
import os


# ==================================================
# MAIN WINDOW
# ==================================================

window = tk.Tk()
window.title("Smart To-Do List")
window.geometry("1050x680")
window.minsize(950, 620)

# Tasks are saved in a dedicated folder inside your home directory so they
# survive closing/reopening the app, no matter where the script itself is
# run from (and even if that folder isn't writable).
TASKS_DIR = os.path.join(os.path.expanduser("~"), ".taskflow")
TASKS_FILE = os.path.join(TASKS_DIR, "tasks_data.json")
_save_warning_shown = [False]


# ==================================================
# COLORS / THEMES
# ==================================================

# Colors that never change between light/dark mode (brand + accents)
DARK = "#0F1626"
DARK_HOVER = "#1F2E4A"

BLUE = "#2563EB"
ORANGE = "#F59E0B"
GREEN = "#16A34A"
RED = "#DC2626"
GOLD = "#B45309"

THEMES = {
    "light": dict(
        BACKGROUND="#F4F6F8",
        WHITE="#FFFFFF",
        TEXT="#0B1220",
        GRAY="#5B6472",
        BORDER="#D9DEE6",
        BLUE_LIGHT="#E8F1FF",
        ORANGE_LIGHT="#FFF3E0",
        GREEN_LIGHT="#E8F8EF",
    ),
    "dark": dict(
        BACKGROUND="#11141C",
        WHITE="#1B212D",
        TEXT="#F1F3F6",
        GRAY="#9AA3B2",
        BORDER="#2B3242",
        BLUE_LIGHT="#1D2A44",
        ORANGE_LIGHT="#3A2E1A",
        GREEN_LIGHT="#183328",
    ),
}

theme_name = ["light"]

# These get reassigned by refresh_theme(); start with light theme values.
BACKGROUND = THEMES["light"]["BACKGROUND"]
WHITE = THEMES["light"]["WHITE"]
TEXT = THEMES["light"]["TEXT"]
GRAY = THEMES["light"]["GRAY"]
BORDER = THEMES["light"]["BORDER"]
BLUE_LIGHT = THEMES["light"]["BLUE_LIGHT"]
ORANGE_LIGHT = THEMES["light"]["ORANGE_LIGHT"]
GREEN_LIGHT = THEMES["light"]["GREEN_LIGHT"]

window.configure(bg=BACKGROUND)


# ==================================================
# VIEW CONFIG
# ==================================================

VIEWS = {
    "dashboard": {
        "label": "Dashboard",
        "greeting": "Good Morning! \U0001F44B",
        "subtitle": "Stay organized and get things done.",
    },
    "mytasks": {
        "label": "My Tasks",
        "greeting": "All Your Tasks",
        "subtitle": "Everything on your plate, in one place.",
    },
    "today": {
        "label": "Today",
        "greeting": "Today's Focus \U0001F3AF",
        "subtitle": "Tasks due today.",
    },
    "important": {
        "label": "Important",
        "greeting": "Starred Tasks \u2B50",
        "subtitle": "The tasks you've marked important.",
    },
    "completed": {
        "label": "Completed",
        "greeting": "Nice Work! \u2705",
        "subtitle": "Tasks you've already finished.",
    },
}


# ==================================================
# SETTINGS STATE (must exist before functions that use it)
# ==================================================

confirm_delete_enabled = tk.BooleanVar(value=True)
dark_mode_enabled = tk.BooleanVar(value=False)


# ==================================================
# SIDEBAR
# ==================================================

sidebar = tk.Frame(window, bg=DARK, width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

logo = tk.Label(
    sidebar, text="\u2713  TaskFlow", font=("Arial", 22, "bold"),
    bg=DARK, fg="#FFFFFF"
)
logo.pack(pady=(35, 45))

sidebar_buttons = {}


def create_sidebar_button(text, filter_key, command):
    button = tk.Button(
        sidebar, text=text, font=("Arial", 12),
        bg=DARK, fg="#FFFFFF", activebackground=DARK_HOVER, activeforeground="#FFFFFF",
        relief="flat", anchor="w", padx=25, width=20, height=2, cursor="hand2",
        command=command
    )
    button.pack(pady=3)
    if filter_key:
        sidebar_buttons[filter_key] = button
    return button


dashboard_button = create_sidebar_button(
    "\u2302   Dashboard", "dashboard", lambda: apply_filter("dashboard")
)
tasks_button = create_sidebar_button(
    "\u2611   My Tasks", "mytasks", lambda: apply_filter("mytasks")
)
today_button = create_sidebar_button(
    "\u25F7   Today", "today", lambda: apply_filter("today")
)
important_button = create_sidebar_button(
    "\u2605   Important", "important", lambda: apply_filter("important")
)
completed_button = create_sidebar_button(
    "\u2713   Completed", "completed", lambda: apply_filter("completed")
)
settings_button = create_sidebar_button(
    "\u2699   Settings", None, lambda: open_settings()
)


def highlight_sidebar_button(filter_key):
    for key, btn in sidebar_buttons.items():
        btn.config(bg=DARK_HOVER if key == filter_key else DARK)


# ==================================================
# MAIN AREA
# ==================================================

main_area = tk.Frame(window, bg=BACKGROUND)
main_area.pack(side="left", fill="both", expand=True)


# ==================================================
# TOP BAR
# ==================================================

top_bar = tk.Frame(main_area, bg=WHITE, height=70)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)

title = tk.Label(
    top_bar, text="Dashboard", font=("Arial", 21, "bold"), bg=WHITE, fg=TEXT
)
title.pack(side="left", padx=30)

user_name = tk.StringVar(value="Student")

user = tk.Label(
    top_bar, text="\U0001F464  Student", font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT
)
user.pack(side="right", padx=30)


def refresh_user_label(*args):
    user.config(text=f"\U0001F464  {user_name.get()}")


user_name.trace_add("write", refresh_user_label)

add_task_button = tk.Button(
    top_bar, text="+  Add Task", font=("Arial", 12, "bold"),
    bg=BLUE, fg="#FFFFFF", activebackground=BLUE, activeforeground="#FFFFFF",
    relief="flat", padx=15, pady=6, cursor="hand2"
)
add_task_button.pack(side="right", padx=10)


# ==================================================
# CONTENT
# ==================================================

content = tk.Frame(main_area, bg=BACKGROUND)
content.pack(fill="both", expand=True, padx=30, pady=25)

greeting = tk.Label(
    content, text="Good Morning! \U0001F44B", font=("Arial", 25, "bold"),
    bg=BACKGROUND, fg=TEXT
)
greeting.pack(anchor="w")

subtitle = tk.Label(
    content, text="Stay organized and get things done.", font=("Arial", 12),
    bg=BACKGROUND, fg=GRAY
)
subtitle.pack(anchor="w", pady=(5, 20))


# ==================================================
# STATISTICS
# ==================================================

stats = tk.Frame(content, bg=BACKGROUND)
stats.pack(fill="x")


def create_card(title_text, number, light_key, number_color):
    card = tk.Frame(stats, bg=THEMES[theme_name[0]][light_key], height=105)
    card.pack(side="left", fill="x", expand=True, padx=6)
    card.pack_propagate(False)

    title_label = tk.Label(
        card, text=title_text, font=("Arial", 10, "bold"),
        bg=THEMES[theme_name[0]][light_key], fg=GRAY
    )
    title_label.pack(anchor="w", padx=20, pady=(15, 0))

    number_label = tk.Label(
        card, text=number, font=("Arial", 27, "bold"),
        bg=THEMES[theme_name[0]][light_key], fg=number_color
    )
    number_label.pack(anchor="w", padx=20)

    # stash refs so refresh_theme() can restyle this card later
    number_label.card_frame = card
    number_label.title_label = title_label
    number_label.light_key = light_key

    return number_label


total_card = create_card("TOTAL TASKS", "0", "BLUE_LIGHT", BLUE)
pending_card = create_card("PENDING", "0", "ORANGE_LIGHT", ORANGE)
completed_card = create_card("COMPLETED", "0", "GREEN_LIGHT", GREEN)


def refresh_stats():
    tasks = [t for t in task_list.winfo_children() if getattr(t, "check_var", None) is not None]
    total = len(tasks)
    completed = sum(1 for t in tasks if t.check_var.get())
    pending = total - completed

    total_card.config(text=str(total))
    pending_card.config(text=str(pending))
    completed_card.config(text=str(completed))

    progress_pct = int((completed / total) * 100) if total else 0
    progress_bar["value"] = progress_pct
    progress_percent.config(text=f"{progress_pct}%")


# ==================================================
# TASK HEADER
# ==================================================

task_header = tk.Frame(content, bg=BACKGROUND)
task_header.pack(fill="x", pady=(30, 12))

task_title = tk.Label(
    task_header, text="My Tasks", font=("Arial", 19, "bold"),
    bg=BACKGROUND, fg=TEXT
)
task_title.pack(side="left")

search_var = tk.StringVar()

search_frame = tk.Frame(
    task_header, bg=WHITE, bd=1, relief="solid",
    highlightbackground=BORDER, highlightthickness=1
)
search_frame.pack(side="right", padx=(0, 5), ipady=5)

search_icon = tk.Label(
    search_frame, text="\U0001F50D", font=("Arial", 10), bg=WHITE, fg=GRAY
)
search_icon.pack(side="left", padx=(10, 0))

search_entry = tk.Entry(
    search_frame, textvariable=search_var, font=("Arial", 11),
    bg=WHITE, fg=TEXT, relief="flat", width=22, bd=0,
    highlightthickness=0, insertbackground=TEXT
)
search_entry.pack(side="left", fill="x", expand=True, padx=8)


# ==================================================
# TASK LIST (scrollable)
# ==================================================

task_list_container = tk.Frame(content, bg=BACKGROUND)
task_list_container.pack(fill="both", expand=True, pady=10)

task_canvas = tk.Canvas(task_list_container, bg=BACKGROUND, highlightthickness=0, bd=0)
task_scrollbar = ttk.Scrollbar(task_list_container, orient="vertical", command=task_canvas.yview)

task_list = tk.Frame(task_canvas, bg=BACKGROUND)
task_list_window_id = task_canvas.create_window((0, 0), window=task_list, anchor="nw")

task_canvas.configure(yscrollcommand=task_scrollbar.set)
task_canvas.pack(side="left", fill="both", expand=True)
task_scrollbar.pack(side="right", fill="y")


def _on_task_list_configure(event):
    task_canvas.configure(scrollregion=task_canvas.bbox("all"))


def _on_canvas_configure(event):
    task_canvas.itemconfig(task_list_window_id, width=event.width)


task_list.bind("<Configure>", _on_task_list_configure)
task_canvas.bind("<Configure>", _on_canvas_configure)


def _on_mousewheel(event):
    task_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def _on_mousewheel_linux(event):
    if event.num == 4:
        task_canvas.yview_scroll(-1, "units")
    elif event.num == 5:
        task_canvas.yview_scroll(1, "units")


def _bind_mousewheel(event):
    task_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    task_canvas.bind_all("<Button-4>", _on_mousewheel_linux)
    task_canvas.bind_all("<Button-5>", _on_mousewheel_linux)


def _unbind_mousewheel(event):
    task_canvas.unbind_all("<MouseWheel>")
    task_canvas.unbind_all("<Button-4>")
    task_canvas.unbind_all("<Button-5>")


task_canvas.bind("<Enter>", _bind_mousewheel)
task_canvas.bind("<Leave>", _unbind_mousewheel)

empty_state_label = tk.Label(
    task_list, text="No tasks match this view.",
    font=("Arial", 12), bg=BACKGROUND, fg=GRAY
)


def get_priority_color(priority):
    if priority == "High":
        return RED
    elif priority == "Medium":
        return ORANGE
    else:
        return GREEN


def get_due_display(due_date_str, is_completed):
    """Returns (text, color) for the due-date line under a task."""
    if not due_date_str:
        return "No due date", GRAY
    try:
        due = datetime.date.fromisoformat(due_date_str)
    except ValueError:
        return f"Due: {due_date_str}", GRAY

    today = datetime.date.today()
    if is_completed:
        return f"Due: {due.isoformat()}", GRAY
    if due < today:
        return f"\u26A0 Overdue: {due.isoformat()}", RED
    if due == today:
        return "\u25CF Due Today", GOLD
    return f"Due: {due.isoformat()}", GRAY


def create_task(task_name, priority_level, due_date="", completed=False, important=False):
    """Create a task row. priority_level is 'High' / 'Medium' / 'Low'."""
    priority_color = get_priority_color(priority_level)

    task = tk.Frame(task_list, bg=WHITE)
    task.pack(fill="x", pady=4)

    check_var = tk.IntVar(value=1 if completed else 0)
    important_var = tk.IntVar(value=1 if important else 0)

    left = tk.Frame(task, bg=WHITE)
    left.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=8)

    top_row = tk.Frame(left, bg=WHITE)
    top_row.pack(fill="x", anchor="w")

    star_button = tk.Label(
        top_row, text="\u2606", font=("Arial", 15), bg=WHITE, fg=GRAY, cursor="hand2"
    )
    star_button.pack(side="left", padx=(0, 5))

    checkbox = tk.Checkbutton(
        top_row, text=task_name, font=("Arial", 13, "bold"),
        bg=WHITE, fg=TEXT, activebackground=WHITE, activeforeground=TEXT,
        selectcolor=WHITE, variable=check_var
    )
    checkbox.pack(side="left")

    due_label = tk.Label(
        left, font=("Arial", 10, "bold"), bg=WHITE, anchor="w"
    )
    due_label.pack(fill="x", anchor="w", padx=(30, 0), pady=(2, 0))

    right = tk.Frame(task, bg=WHITE)
    right.pack(side="right", padx=10, pady=8)

    priority_label = tk.Label(
        right, text=priority_level.upper(), font=("Arial", 10, "bold"),
        bg=priority_color, fg="#FFFFFF", padx=9, pady=4
    )
    priority_label.pack(side="left", padx=(0, 10))

    edit_button = tk.Label(
        right, text="\u270F\uFE0F", font=("Arial", 13), bg=WHITE, cursor="hand2"
    )
    edit_button.pack(side="left", padx=5)

    delete_button = tk.Label(
        right, text="\U0001F5D1\uFE0F", font=("Arial", 13), bg=WHITE, cursor="hand2"
    )
    delete_button.pack(side="left", padx=5)

    # Stash state/refs on the frame for filters, search, edit, delete, theming.
    task.check_var = check_var
    task.important_var = important_var
    task.due_date = due_date
    task.task_name = task_name
    task.priority_level = priority_level
    task.checkbox = checkbox
    task.due_label = due_label
    task.priority_label = priority_label
    task.star_button = star_button
    task.left = left
    task.top_row = top_row
    task.right_frame = right
    task.edit_button = edit_button
    task.delete_button = delete_button

    def refresh_row_display():
        due_text, due_color = get_due_display(task.due_date, bool(check_var.get()))
        due_label.config(text=due_text, fg=due_color)
        star_button.config(
            text="\u2605" if important_var.get() else "\u2606",
            fg=GOLD if important_var.get() else GRAY
        )

    def on_check_toggle():
        refresh_row_display()
        refresh_stats()
        search_tasks()
        save_tasks_to_file()

    def toggle_important(event=None):
        important_var.set(0 if important_var.get() else 1)
        refresh_row_display()
        search_tasks()
        save_tasks_to_file()

    checkbox.config(command=on_check_toggle)
    star_button.bind("<Button-1>", toggle_important)
    edit_button.bind("<Button-1>", lambda e: open_task_form(task))
    delete_button.bind("<Button-1>", lambda e: delete_task(task))

    task.refresh_row_display = refresh_row_display
    refresh_row_display()
    refresh_stats()
    return task


def apply_theme_to_task(task):
    """Re-color an existing task row to match the current theme."""
    task.configure(bg=WHITE)
    task.left.configure(bg=WHITE)
    task.top_row.configure(bg=WHITE)
    task.star_button.configure(bg=WHITE)
    task.checkbox.configure(
        bg=WHITE, fg=TEXT, activebackground=WHITE, activeforeground=TEXT, selectcolor=WHITE
    )
    task.due_label.configure(bg=WHITE)
    task.right_frame.configure(bg=WHITE)
    task.edit_button.configure(bg=WHITE)
    task.delete_button.configure(bg=WHITE)
    task.refresh_row_display()


def update_task(task, task_name, priority_level, due_date):
    task.task_name = task_name
    task.priority_level = priority_level
    task.due_date = due_date
    task.checkbox.config(text=task_name)
    task.priority_label.config(
        text=priority_level.upper(), bg=get_priority_color(priority_level)
    )
    task.refresh_row_display()
    refresh_stats()
    search_tasks()
    save_tasks_to_file()


def delete_task(task):
    if confirm_delete_enabled.get():
        confirmed = messagebox.askyesno(
            "Delete Task", f'Delete "{task.task_name}"?', parent=window
        )
        if not confirmed:
            return
    task.destroy()
    refresh_stats()
    search_tasks()
    save_tasks_to_file()


# ==================================================
# SEARCH + SIDEBAR FILTER
# ==================================================

current_filter = ["dashboard"]


def apply_filter(filter_key):
    current_filter[0] = filter_key
    highlight_sidebar_button(filter_key)

    view = VIEWS[filter_key]
    title.config(text=view["label"])
    task_title.config(text=view["label"] if filter_key != "dashboard" else "My Tasks")
    greeting.config(text=view["greeting"])
    subtitle.config(text=view["subtitle"])

    search_tasks()


def search_tasks(*args):
    search_text = search_var.get().lower()
    today_str = datetime.date.today().isoformat()

    all_tasks = [t for t in task_list.winfo_children() if hasattr(t, "task_name")]
    for task in all_tasks:
        task.pack_forget()

    visible_count = 0
    for task in all_tasks:
        matches_search = search_text in task.task_name.lower()

        filter_key = current_filter[0]
        if filter_key == "completed":
            matches_filter = bool(task.check_var.get())
        elif filter_key == "important":
            matches_filter = bool(task.important_var.get())
        elif filter_key == "today":
            matches_filter = task.due_date == today_str
        else:
            matches_filter = True

        if matches_search and matches_filter:
            task.pack(fill="x", pady=4)
            visible_count += 1

    if visible_count == 0:
        empty_state_label.pack(pady=30)
    else:
        empty_state_label.pack_forget()

    task_canvas.update_idletasks()
    task_canvas.configure(scrollregion=task_canvas.bbox("all"))


search_var.trace_add("write", search_tasks)


# ==================================================
# CALENDAR DATE PICKER (no external packages needed)
# ==================================================

def open_calendar_picker(target_entry, parent_window):
    today = datetime.date.today()
    state = {"year": today.year, "month": today.month}

    picker = tk.Toplevel(parent_window)
    picker.title("Select Date")
    picker.configure(bg=WHITE)
    picker.resizable(False, False)
    picker.transient(parent_window)
    picker.grab_set()

    header = tk.Frame(picker, bg=WHITE)
    header.pack(fill="x", padx=10, pady=10)

    def change_month(delta):
        m = state["month"] + delta
        y = state["year"]
        if m < 1:
            m, y = 12, y - 1
        elif m > 12:
            m, y = 1, y + 1
        state["month"], state["year"] = m, y
        draw_calendar()

    prev_btn = tk.Button(
        header, text="<", font=("Arial", 11, "bold"), relief="flat",
        bg=WHITE, fg=TEXT, cursor="hand2", command=lambda: change_month(-1)
    )
    prev_btn.pack(side="left")

    month_label = tk.Label(header, font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT)
    month_label.pack(side="left", expand=True)

    next_btn = tk.Button(
        header, text=">", font=("Arial", 11, "bold"), relief="flat",
        bg=WHITE, fg=TEXT, cursor="hand2", command=lambda: change_month(1)
    )
    next_btn.pack(side="right")

    days_frame = tk.Frame(picker, bg=WHITE)
    days_frame.pack(padx=10, pady=(0, 10))

    def pick_day(day):
        date_str = f"{state['year']:04d}-{state['month']:02d}-{day:02d}"
        target_entry.delete(0, tk.END)
        target_entry.insert(0, date_str)
        picker.destroy()

    def draw_calendar():
        for widget in days_frame.winfo_children():
            widget.destroy()

        month_label.config(
            text=f"{cal_module.month_name[state['month']]} {state['year']}"
        )

        for i, wd in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(
                days_frame, text=wd, font=("Arial", 9, "bold"),
                bg=WHITE, fg=GRAY, width=4
            ).grid(row=0, column=i, pady=(0, 4))

        month_days = cal_module.Calendar(firstweekday=0).monthdayscalendar(
            state["year"], state["month"]
        )
        for r, week in enumerate(month_days, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(days_frame, text="", width=4, bg=WHITE).grid(row=r, column=c)
                    continue
                is_today = (
                    day == today.day and state["month"] == today.month
                    and state["year"] == today.year
                )
                tk.Button(
                    days_frame, text=str(day), width=4, relief="flat",
                    bg=BLUE_LIGHT if is_today else WHITE,
                    fg=BLUE if is_today else TEXT,
                    font=("Arial", 10, "bold" if is_today else "normal"),
                    cursor="hand2", command=lambda d=day: pick_day(d)
                ).grid(row=r, column=c, padx=1, pady=1)

    draw_calendar()


# ==================================================
# ADD / EDIT TASK WINDOW (shared form)
# ==================================================

def open_task_form(existing_task=None):
    is_editing = existing_task is not None

    form_window = tk.Toplevel(window)
    form_window.title("Edit Task" if is_editing else "Add New Task")
    form_window.geometry("480x520")
    form_window.configure(bg=WHITE)
    form_window.resizable(False, False)

    heading = tk.Label(
        form_window, text="Edit Task" if is_editing else "Add New Task",
        font=("Arial", 22, "bold"), bg=WHITE, fg=TEXT
    )
    heading.pack(pady=(25, 20))

    task_label = tk.Label(
        form_window, text="Task Name", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT
    )
    task_label.pack(anchor="w", padx=40)

    task_entry = tk.Entry(form_window, font=("Arial", 12), width=35)
    task_entry.pack(padx=40, pady=(5, 15), ipady=7)

    priority_label = tk.Label(
        form_window, text="Priority", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT
    )
    priority_label.pack(anchor="w", padx=40)

    priority = ttk.Combobox(
        form_window, values=["High", "Medium", "Low"],
        state="readonly", font=("Arial", 11), width=32
    )
    priority.pack(padx=40, pady=(5, 20), ipady=5)

    date_label = tk.Label(
        form_window, text="Due Date", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT
    )
    date_label.pack(anchor="w", padx=40)

    date_row = tk.Frame(form_window, bg=WHITE)
    date_row.pack(padx=40, pady=(5, 20), fill="x")

    date_entry = tk.Entry(date_row, font=("Arial", 12))
    date_entry.pack(side="left", fill="x", expand=True, ipady=7)

    calendar_button = tk.Button(
        date_row, text="\U0001F4C5", font=("Arial", 11), relief="flat",
        bg=BORDER, fg=TEXT, cursor="hand2",
        command=lambda: open_calendar_picker(date_entry, form_window)
    )
    calendar_button.pack(side="left", padx=(8, 0), ipady=5, ipadx=4)

    if is_editing:
        task_entry.insert(0, existing_task.task_name)
        priority.set(existing_task.priority_level)
        date_entry.insert(0, existing_task.due_date)
    else:
        priority.set("Medium")

    error_label = tk.Label(form_window, text="", font=("Arial", 9), bg=WHITE, fg=RED)
    error_label.pack()

    def save_task():
        task_name = task_entry.get().strip()
        selected_priority = priority.get()
        due_date = date_entry.get().strip()

        if task_name == "":
            error_label.config(text="Please enter a task name.")
            return

        if due_date:
            try:
                datetime.date.fromisoformat(due_date)
            except ValueError:
                error_label.config(text="Due date must be in YYYY-MM-DD format.")
                return

        if is_editing:
            update_task(existing_task, task_name, selected_priority, due_date)
        else:
            create_task(task_name, selected_priority, due_date)
            search_tasks()
            save_tasks_to_file()

        form_window.destroy()

    save_button = tk.Button(
        form_window, text="Save Changes" if is_editing else "Save Task",
        font=("Arial", 11, "bold"),
        bg=BLUE, fg="#FFFFFF", relief="flat", padx=20, pady=8,
        cursor="hand2", command=save_task
    )
    save_button.pack(pady=10)


add_task_button.config(command=lambda: open_task_form())


# ==================================================
# THEME (DARK / LIGHT MODE)
# ==================================================

def refresh_theme():
    """Reads theme_name[0] and restyles every persistent widget + task row."""
    global BACKGROUND, WHITE, TEXT, GRAY, BORDER, BLUE_LIGHT, ORANGE_LIGHT, GREEN_LIGHT
    t = THEMES[theme_name[0]]
    BACKGROUND = t["BACKGROUND"]
    WHITE = t["WHITE"]
    TEXT = t["TEXT"]
    GRAY = t["GRAY"]
    BORDER = t["BORDER"]
    BLUE_LIGHT = t["BLUE_LIGHT"]
    ORANGE_LIGHT = t["ORANGE_LIGHT"]
    GREEN_LIGHT = t["GREEN_LIGHT"]

    window.configure(bg=BACKGROUND)
    main_area.configure(bg=BACKGROUND)

    top_bar.configure(bg=WHITE)
    title.configure(bg=WHITE, fg=TEXT)
    user.configure(bg=WHITE, fg=TEXT)

    content.configure(bg=BACKGROUND)
    greeting.configure(bg=BACKGROUND, fg=TEXT)
    subtitle.configure(bg=BACKGROUND, fg=GRAY)
    stats.configure(bg=BACKGROUND)

    for label in (total_card, pending_card, completed_card):
        bg_color = t[label.light_key]
        label.card_frame.configure(bg=bg_color)
        label.title_label.configure(bg=bg_color, fg=GRAY)
        label.configure(bg=bg_color)

    task_header.configure(bg=BACKGROUND)
    task_title.configure(bg=BACKGROUND, fg=TEXT)
    search_frame.configure(bg=WHITE, highlightbackground=BORDER)
    search_icon.configure(bg=WHITE, fg=GRAY)
    search_entry.configure(bg=WHITE, fg=TEXT, insertbackground=TEXT)

    task_list_container.configure(bg=BACKGROUND)
    task_canvas.configure(bg=BACKGROUND)
    task_list.configure(bg=BACKGROUND)
    empty_state_label.configure(bg=BACKGROUND, fg=GRAY)

    progress_frame.configure(bg=WHITE)
    progress_text.configure(bg=WHITE, fg=TEXT)
    progress_percent.configure(bg=WHITE)

    for task in task_list.winfo_children():
        if hasattr(task, "task_name"):
            apply_theme_to_task(task)


def toggle_dark_mode(settings_window=None):
    theme_name[0] = "dark" if dark_mode_enabled.get() else "light"
    refresh_theme()
    # Rebuild the settings window itself so it picks up the new colors too.
    if settings_window is not None and settings_window.winfo_exists():
        settings_window.destroy()
        open_settings()


# ==================================================
# SETTINGS PANEL
# ==================================================

def open_settings():
    settings_window = tk.Toplevel(window)
    settings_window.title("Settings")
    settings_window.geometry("440x480")
    settings_window.configure(bg=WHITE)
    settings_window.resizable(False, False)

    heading = tk.Label(
        settings_window, text="\u2699\uFE0F Settings", font=("Arial", 20, "bold"),
        bg=WHITE, fg=TEXT
    )
    heading.pack(pady=(25, 20))

    body = tk.Frame(settings_window, bg=WHITE)
    body.pack(fill="both", expand=True, padx=40)

    # ---- Display Name ----
    name_label = tk.Label(
        body, text="Display Name", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT
    )
    name_label.pack(anchor="w")

    name_row = tk.Frame(body, bg=WHITE)
    name_row.pack(fill="x", pady=(5, 18))

    name_entry = tk.Entry(name_row, font=("Arial", 12))
    name_entry.insert(0, user_name.get())
    name_entry.pack(side="left", fill="x", expand=True, ipady=6)

    name_status = tk.Label(body, text="", font=("Arial", 9), bg=WHITE)
    name_status.pack(anchor="w")

    def save_name():
        new_name = name_entry.get().strip()
        if new_name:
            user_name.set(new_name)
            name_status.config(text="Saved.", fg=GREEN)
        else:
            name_status.config(text="Name can't be empty.", fg=RED)

    save_name_button = tk.Button(
        name_row, text="Save", font=("Arial", 10, "bold"),
        bg=BLUE, fg="#FFFFFF", relief="flat", padx=12, pady=4,
        cursor="hand2", command=save_name
    )
    save_name_button.pack(side="left", padx=(8, 0))

    ttk.Separator(body, orient="horizontal").pack(fill="x", pady=10)

    # ---- Dark / Light Mode ----
    dark_check = tk.Checkbutton(
        body, text="\U0001F319  Dark Mode", font=("Arial", 11, "bold"),
        bg=WHITE, fg=TEXT, activebackground=WHITE, activeforeground=TEXT,
        selectcolor=WHITE, variable=dark_mode_enabled,
        command=lambda: toggle_dark_mode(settings_window)
    )
    dark_check.pack(anchor="w", pady=6)

    # ---- Confirm Delete ----
    confirm_check = tk.Checkbutton(
        body, text="\U0001F5D1\uFE0F  Confirm Before Delete", font=("Arial", 11, "bold"),
        bg=WHITE, fg=TEXT, activebackground=WHITE, activeforeground=TEXT,
        selectcolor=WHITE, variable=confirm_delete_enabled
    )
    confirm_check.pack(anchor="w", pady=6)

    ttk.Separator(body, orient="horizontal").pack(fill="x", pady=10)

    # ---- Clear Completed Tasks ----
    def clear_completed_tasks():
        completed_tasks = [
            t for t in task_list.winfo_children()
            if hasattr(t, "task_name") and t.check_var.get()
        ]
        if not completed_tasks:
            messagebox.showinfo(
                "Clear Completed", "No completed tasks to clear.", parent=settings_window
            )
            return
        confirmed = messagebox.askyesno(
            "Clear Completed Tasks",
            f"Delete {len(completed_tasks)} completed task(s)? This cannot be undone.",
            parent=settings_window
        )
        if confirmed:
            for t in completed_tasks:
                t.destroy()
            refresh_stats()
            search_tasks()
            save_tasks_to_file()

    clear_button = tk.Button(
        body, text="\U0001F9F9  Clear Completed Tasks", font=("Arial", 10, "bold"),
        bg=ORANGE, fg="#FFFFFF", relief="flat", padx=12, pady=6,
        cursor="hand2", command=clear_completed_tasks
    )
    clear_button.pack(anchor="w", pady=(4, 10))

    # ---- About ----
    def show_about():
        messagebox.showinfo(
            "About TaskFlow",
            "TaskFlow \u2014 Smart To-Do List\nVersion 1.1\n\n"
            "Organize tasks, set priorities, and pick due dates to stay "
            "on top of everything on your plate.",
            parent=settings_window
        )

    about_button = tk.Button(
        body, text="\u2139\uFE0F  About", font=("Arial", 10, "bold"),
        bg=GRAY, fg="#FFFFFF", relief="flat", padx=12, pady=6,
        cursor="hand2", command=show_about
    )
    about_button.pack(anchor="w", pady=(0, 10))

    close_button = tk.Button(
        settings_window, text="Close", font=("Arial", 10, "bold"),
        bg=DARK, fg="#FFFFFF", relief="flat", padx=15, pady=6,
        cursor="hand2", command=settings_window.destroy
    )
    close_button.pack(pady=10)


# ==================================================
# PROGRESS (must exist BEFORE any create_task() calls)
# ==================================================

progress_frame = tk.Frame(content, bg=WHITE, height=65)
progress_frame.pack(fill="x", pady=(5, 0))
progress_frame.pack_propagate(False)

progress_text = tk.Label(
    progress_frame, text="Today's Progress", font=("Arial", 11, "bold"),
    bg=WHITE, fg=TEXT
)
progress_text.pack(side="left", padx=20)

progress_bar = ttk.Progressbar(progress_frame, length=250, value=0, mode="determinate")
progress_bar.pack(side="left", padx=20)

progress_percent = tk.Label(
    progress_frame, text="0%", font=("Arial", 11, "bold"), bg=WHITE, fg=GREEN
)
progress_percent.pack(side="left")


# ==================================================
# SAVE / LOAD TASKS (persist across app restarts)
# ==================================================

def save_tasks_to_file():
    tasks_data = []
    for t in task_list.winfo_children():
        if hasattr(t, "task_name"):
            tasks_data.append({
                "name": t.task_name,
                "priority": t.priority_level,
                "due_date": t.due_date,
                "completed": bool(t.check_var.get()),
                "important": bool(t.important_var.get()),
            })
    try:
        os.makedirs(TASKS_DIR, exist_ok=True)
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, indent=2)
    except OSError as e:
        if not _save_warning_shown[0]:
            _save_warning_shown[0] = True
            messagebox.showwarning(
                "Couldn't Save Tasks",
                "TaskFlow can't write to its save file, so your tasks won't "
                f"be remembered after you close the app.\n\nDetails: {e}\n\n"
                f"Save location: {TASKS_FILE}",
                parent=window
            )


def load_tasks_from_file():
    if not os.path.exists(TASKS_FILE):
        return None
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        messagebox.showwarning(
            "Couldn't Load Saved Tasks",
            "Your saved tasks file exists but couldn't be read, so TaskFlow "
            f"is starting fresh instead of overwriting it.\n\nDetails: {e}\n\n"
            f"File: {TASKS_FILE}",
            parent=window
        )
        return []


# ==================================================
# LOAD EXISTING TASKS (or seed sample tasks on first run)
# ==================================================

_saved_tasks = load_tasks_from_file()

if _saved_tasks is not None:
    for _t in _saved_tasks:
        create_task(
            _t.get("name", ""),
            _t.get("priority", "Medium"),
            _t.get("due_date", ""),
            completed=_t.get("completed", False),
            important=_t.get("important", False),
        )
else:
    _today = datetime.date.today()
    create_task("Complete Python Mini Project", "High", _today.isoformat())
    create_task("Submit DBMS Assignment", "Medium", (_today + datetime.timedelta(days=2)).isoformat())
    create_task("Prepare Mathematics Notes", "Low", "")
    save_tasks_to_file()

refresh_user_label()
apply_filter("dashboard")


# ==================================================
# START APPLICATION
# ==================================================

window.mainloop()