import sys
import os
import pyperclip
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTextEdit,
    QPushButton, QComboBox, QLabel, QMessageBox, QStackedWidget, QFrame,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QProgressBar, QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRegExp
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from lessons import lessons
from grader.grading import grade_submission, GradeResult
from progress.db import (
    init_db, record_attempt, get_struggling_topics, get_dashboard_stats,
    get_completed_topics, DEFAULT_LEARNER_ID,
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "progress.db")

# ---------------------------------------------------------------- Color palette

COLORS = {
    "bg": "#0f1117",
    "panel": "#171a24",
    "card": "#1c2030",
    "border": "#2a2e3d",
    "text": "#e5e7eb",
    "text_dim": "#9ca3af",
    "green": "#22c55e",
    "orange": "#f59e0b",
    "purple": "#a855f7",
    "blue": "#3b82f6",
    "red": "#ef4444",
}

LEVEL_COLORS = {
    "Beginner": COLORS["green"],
    "Intermediate": COLORS["orange"],
    "Advanced": COLORS["purple"],
}

STYLESHEET = f"""
QWidget {{
    background-color: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: "Segoe UI", "Cantarell", sans-serif;
    font-size: 13px;
}}
QFrame#card, QFrame#sidebar, QFrame#topBar {{
    background-color: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}
QLabel#pageTitle {{
    font-size: 20px;
    font-weight: bold;
}}
QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {COLORS["text_dim"]};
}}
QLabel#statNumber {{
    font-size: 22px;
    font-weight: bold;
}}
QLabel#statLabel {{
    color: {COLORS["text_dim"]};
    font-size: 11px;
}}
QLabel#levelBadge {{
    background-color: {COLORS["green"]};
    color: #0f1117;
    border-radius: 8px;
    padding: 2px 10px;
    font-weight: bold;
}}
QPushButton {{
    background-color: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px 14px;
}}
QPushButton:hover {{
    border-color: {COLORS["blue"]};
}}
QPushButton#primaryButton {{
    background-color: {COLORS["green"]};
    color: #0f1117;
    font-weight: bold;
    border: none;
}}
QPushButton#primaryButton:hover {{
    background-color: #16a34a;
}}
QComboBox, QTextEdit {{
    background-color: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 6px;
}}
QTreeWidget {{
    background-color: {COLORS["panel"]};
    border: none;
    outline: none;
}}
QTreeWidget::item {{
    padding: 5px 4px;
    border-radius: 6px;
    font-size: 12px;
}}
QTreeWidget::item:selected {{
    background-color: {COLORS["card"]};
    color: {COLORS["green"]};
}}
QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {COLORS["panel"]};
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: {COLORS["text_dim"]};
}}
QTabBar::tab:selected {{
    background-color: {COLORS["card"]};
    color: {COLORS["green"]};
    font-weight: bold;
}}
QProgressBar {{
    background-color: {COLORS["card"]};
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: {COLORS["text"]};
}}
QProgressBar::chunk {{
    border-radius: 6px;
}}
QProgressBar#beginnerBar::chunk {{ background-color: {COLORS["green"]}; }}
QProgressBar#intermediateBar::chunk {{ background-color: {COLORS["orange"]}; }}
QProgressBar#advancedBar::chunk {{ background-color: {COLORS["purple"]}; }}
QScrollBar:vertical {{
    background: {COLORS["panel"]};
    width: 14px;
    margin: 0px;
    border-radius: 7px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    min-height: 24px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS["blue"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    border: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: {COLORS["panel"]};
    height: 14px;
    margin: 0px;
    border-radius: 7px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS["border"]};
    min-width: 24px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS["blue"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    border: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""


# ---------------------------------------------------------------- Syntax highlighting

class PythonHighlighter(QSyntaxHighlighter):
    """
    A lightweight, regex-based Python syntax highlighter — not a full
    tokenizer, but enough to give the code sample a professional look
    (keywords, strings, comments, numbers colored distinctly).
    """

    def __init__(self, document):
        super().__init__(document)
        self._rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c678dd"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "def", "return", "if", "elif", "else", "for", "while", "in", "not",
            "and", "or", "class", "import", "from", "as", "try", "except",
            "finally", "raise", "with", "yield", "lambda", "pass", "break",
            "continue", "global", "nonlocal", "is", "None", "True", "False",
            "self", "assert", "del", "async", "await",
        ]
        for kw in keywords:
            self._rules.append((QRegExp(r"\b" + kw + r"\b"), keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98c379"))
        self._rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self._rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#d19a66"))
        self._rules.append((QRegExp(r"\b[0-9]+\.?[0-9]*\b"), number_format))

        # Comments last, so a '#' inside a string doesn't get overridden by this rule
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5c6370"))
        comment_format.setFontItalic(True)
        self._rules.append((QRegExp(r"#[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)


# ---------------------------------------------------------------- Circular progress widget

class CircularProgress(QWidget):
    """A simple ring-shaped progress indicator with a centered percentage label."""

    def __init__(self, value=0, size=120, thickness=12, color=COLORS["green"], parent=None):
        super().__init__(parent)
        self._value = value
        self._size = size
        self._thickness = thickness
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def set_value(self, value):
        self._value = max(0, min(100, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = self._thickness / 2
        rect = self.rect().adjusted(int(margin), int(margin), -int(margin), -int(margin))

        bg_pen = QPen(QColor(COLORS["border"]))
        bg_pen.setWidth(self._thickness)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        fg_pen = QPen(self._color)
        fg_pen.setWidth(self._thickness)
        fg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(fg_pen)
        span = int(self._value / 100 * 360 * 16)
        painter.drawArc(rect, 90 * 16, -span)

        painter.setPen(QColor(COLORS["text"]))
        font = painter.font()
        font.setPointSize(15)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{int(self._value)}%")


def _stat_card(number_text: str, label_text: str) -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    layout = QVBoxLayout(card)
    number = QLabel(number_text)
    number.setObjectName("statNumber")
    number.setAlignment(Qt.AlignCenter)
    label = QLabel(label_text)
    label.setObjectName("statLabel")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(number)
    layout.addWidget(label)
    return card


# ---------------------------------------------------------------- Grading worker (background thread)

class GradingWorker(QThread):
    """
    Runs grade_submission (which involves running the sandbox and can take
    up to a few seconds) on a separate thread — so the main UI doesn't
    freeze while the code is being checked.
    """
    finished = pyqtSignal(object)  # GradeResult

    def __init__(self, topic: str, user_code: str):
        super().__init__()
        self.topic = topic
        self.user_code = user_code

    def run(self):
        result = grade_submission(self.topic, self.user_code, lessons)
        self.finished.emit(result)


# ---------------------------------------------------------------- Dashboard page

class DashboardPage(QWidget):
    def __init__(self, on_start_learning):
        super().__init__()
        self._on_start_learning = on_start_learning

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("👋 Welcome back!")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("Let's continue your Python learning journey.")
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(subtitle)

        # --- Level progress card ---
        level_card = QFrame()
        level_card.setObjectName("card")
        level_layout = QVBoxLayout(level_card)
        level_title = QLabel("Your Level Progress")
        level_title.setObjectName("sectionTitle")
        level_layout.addWidget(level_title)

        self._level_bars = {}
        self._level_labels = {}
        for level, bar_id in (("Beginner", "beginnerBar"), ("Intermediate", "intermediateBar"), ("Advanced", "advancedBar")):
            row = QHBoxLayout()
            name_label = QLabel(level)
            name_label.setFixedWidth(100)
            bar = QProgressBar()
            bar.setObjectName(bar_id)
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            count_label = QLabel("0 / 0")
            count_label.setFixedWidth(70)
            row.addWidget(name_label)
            row.addWidget(bar)
            row.addWidget(count_label)
            level_layout.addLayout(row)
            self._level_bars[level] = bar
            self._level_labels[level] = count_label

        layout.addWidget(level_card)

        # --- Overall ring + stat cards ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        ring_card = QFrame()
        ring_card.setObjectName("card")
        ring_layout = QVBoxLayout(ring_card)
        ring_title = QLabel("Overall Progress")
        ring_title.setObjectName("sectionTitle")
        ring_title.setAlignment(Qt.AlignCenter)
        self._ring = CircularProgress(value=0)
        ring_inner = QHBoxLayout()
        ring_inner.addStretch()
        ring_inner.addWidget(self._ring)
        ring_inner.addStretch()
        ring_layout.addWidget(ring_title)
        ring_layout.addLayout(ring_inner)
        stats_row.addWidget(ring_card, stretch=1)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)
        self._lessons_card = _stat_card("0", "Lessons Completed")
        self._exercises_card = _stat_card("0", "Exercises Solved")
        self._correct_card = _stat_card("0%", "Correct Answers")
        self._streak_card = _stat_card("0 🔥", "Day Streak")
        cards_grid.addWidget(self._lessons_card, 0, 0)
        cards_grid.addWidget(self._exercises_card, 0, 1)
        cards_grid.addWidget(self._correct_card, 1, 0)
        cards_grid.addWidget(self._streak_card, 1, 1)
        cards_wrapper = QWidget()
        cards_wrapper.setLayout(cards_grid)
        stats_row.addWidget(cards_wrapper, stretch=2)

        layout.addLayout(stats_row)

        start_button = QPushButton("Start Learning →")
        start_button.setObjectName("primaryButton")
        start_button.clicked.connect(self._on_start_learning)
        layout.addWidget(start_button)

        # --- Topics that need more practice ---
        practice_card = QFrame()
        practice_card.setObjectName("card")
        practice_layout = QVBoxLayout(practice_card)
        practice_title = QLabel("📊 Topics to Practice")
        practice_title.setObjectName("sectionTitle")
        practice_layout.addWidget(practice_title)

        self._practice_list_layout = QVBoxLayout()
        practice_layout.addLayout(self._practice_list_layout)
        layout.addWidget(practice_card, stretch=1)

    def _rebuild_practice_list(self):
        # clear any previously shown rows before repopulating
        while self._practice_list_layout.count():
            child = self._practice_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        struggling = get_struggling_topics(DB_PATH, learner_id=DEFAULT_LEARNER_ID)

        if not struggling:
            placeholder = QLabel(
                "Complete a few exercises and personalized suggestions will show up here."
            )
            placeholder.setStyleSheet(f"color: {COLORS['text_dim']};")
            placeholder.setWordWrap(True)
            self._practice_list_layout.addWidget(placeholder)
            return

        for stat in struggling:
            pct = round(stat.pass_rate * 100)
            text = f"• {stat.topic} — {pct}% success ({stat.total_attempts} attempts)"
            if stat.most_common_error:
                text += f" — most common error: {stat.most_common_error}"
            row = QLabel(text)
            row.setWordWrap(True)
            self._practice_list_layout.addWidget(row)

    def refresh(self):
        stats = get_dashboard_stats(DB_PATH, lessons, learner_id=DEFAULT_LEARNER_ID)

        for level, bar in self._level_bars.items():
            total, done = stats["level_progress"].get(level, (0, 0))
            percent = int(done / total * 100) if total else 0
            bar.setValue(percent)
            self._level_labels[level].setText(f"{done} / {total}")

        self._ring.set_value(stats["overall_percent"])
        self._update_card(self._lessons_card, str(stats["lessons_completed"]))
        self._update_card(self._exercises_card, str(stats["exercises_solved"]))
        self._update_card(self._correct_card, f"{int(stats['correct_percent'])}%")
        self._update_card(self._streak_card, f"{stats['day_streak']} 🔥")
        self._rebuild_practice_list()

    @staticmethod
    def _update_card(card: QFrame, number_text: str):
        number_label = card.findChild(QLabel, "statNumber")
        if number_label:
            number_label.setText(number_text)


# ---------------------------------------------------------------- Lesson page

class LessonPage(QWidget):
    def __init__(self, on_back_to_dashboard):
        super().__init__()
        self._on_back_to_dashboard = on_back_to_dashboard
        self._current_topic = None
        self._worker = None  # kept as a reference so GC doesn't collect it mid-run

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(290)
        sidebar_layout = QVBoxLayout(sidebar)

        back_button = QPushButton("← Back to Dashboard")
        back_button.clicked.connect(self._on_back_to_dashboard)
        sidebar_layout.addWidget(back_button)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        sidebar_layout.addWidget(self._tree)

        root_layout.addWidget(sidebar)

        # --- Main content ---
        content = QVBoxLayout()
        content.setSpacing(12)

        header_row = QHBoxLayout()
        self._title_label = QLabel("Select a topic")
        self._title_label.setObjectName("pageTitle")
        self._level_badge = QLabel("")
        self._level_badge.setObjectName("levelBadge")
        header_row.addWidget(self._title_label)
        header_row.addWidget(self._level_badge)
        header_row.addStretch()
        content.addLayout(header_row)

        self._tabs = QTabWidget()

        self._explanation_view = QTextEdit()
        self._explanation_view.setReadOnly(True)
        self._tabs.addTab(self._explanation_view, "📖 Explanation")

        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        self._code_view = QTextEdit()
        self._code_view.setReadOnly(True)
        self._code_view.setFontFamily("Consolas")
        self._highlighter = PythonHighlighter(self._code_view.document())
        self._copy_button = QPushButton("📋 Copy code")
        self._copy_button.clicked.connect(self.copy_code)
        code_layout.addWidget(self._code_view)
        code_layout.addWidget(self._copy_button)
        self._tabs.addTab(code_tab, "💻 Code Example")

        exercise_tab = QWidget()
        exercise_layout = QVBoxLayout(exercise_tab)
        self._exercise_label = QLabel("")
        self._exercise_label.setWordWrap(True)
        exercise_layout.addWidget(self._exercise_label)
        exercise_layout.addWidget(QLabel("Your answer:"))
        self._answer_input = QTextEdit()
        exercise_layout.addWidget(self._answer_input)

        button_row = QHBoxLayout()
        self._check_button = QPushButton("Check Answer ✅")
        self._check_button.setObjectName("primaryButton")
        self._check_button.clicked.connect(self.check_answer)
        button_row.addWidget(self._check_button)
        exercise_layout.addLayout(button_row)

        self._status_label = QLabel("")
        exercise_layout.addWidget(self._status_label)
        self._result_view = QTextEdit()
        self._result_view.setReadOnly(True)
        exercise_layout.addWidget(self._result_view)

        self._tabs.addTab(exercise_tab, "📝 Exercise")

        content.addWidget(self._tabs)
        root_layout.addLayout(content, stretch=1)

        self._populate_tree()

    # ---------------------------------------------------------------- Sidebar / navigation

    def _populate_tree(self):
        self._tree.clear()
        completed = get_completed_topics(DB_PATH, learner_id=DEFAULT_LEARNER_ID)

        for level in ("Beginner", "Intermediate", "Advanced"):
            level_item = QTreeWidgetItem([level])
            level_item.setFlags(Qt.ItemIsEnabled)  # not selectable, just a section header
            font = level_item.font(0)
            font.setBold(True)
            level_item.setFont(0, font)
            level_item.setForeground(0, QColor(LEVEL_COLORS[level]))

            for topic, data in lessons.items():
                if data["level"] != level:
                    continue
                mark = "✓ " if topic in completed else "○ "
                topic_item = QTreeWidgetItem([mark + topic])
                topic_item.setData(0, Qt.UserRole, topic)
                topic_item.setToolTip(0, topic)
                level_item.addChild(topic_item)

            self._tree.addTopLevelItem(level_item)
            level_item.setExpanded(True)

    def _on_tree_item_clicked(self, item, _column):
        topic = item.data(0, Qt.UserRole)
        if topic:
            self.show_lesson(topic)

    def refresh(self):
        """Called whenever this page becomes visible, to reflect any new completions."""
        self._populate_tree()

    # ---------------------------------------------------------------- Lesson display

    def show_lesson(self, topic: str):
        self._current_topic = topic
        lesson = lessons[topic]

        self._title_label.setText(topic)
        self._level_badge.setText(lesson["level"])
        self._level_badge.setStyleSheet(
            f"background-color: {LEVEL_COLORS[lesson['level']]}; color: #0f1117; "
            f"border-radius: 8px; padding: 2px 10px; font-weight: bold;"
        )

        self._explanation_view.setPlainText(lesson["text"])
        self._code_view.setPlainText(lesson["code"])
        self._exercise_label.setText(lesson["exercise"])
        self._result_view.clear()
        self._status_label.setText("")
        self._answer_input.clear()

        auto_gradable = lesson.get("auto_gradable", True)
        self._check_button.setEnabled(auto_gradable)
        if not auto_gradable:
            self._result_view.setPlainText(
                "ℹ️ This exercise has a graphical interface (GUI) and can't be "
                "checked automatically. Run your code and see the result yourself."
            )

        self._tabs.setCurrentIndex(0)

    def copy_code(self):
        if not self._current_topic:
            return
        code = lessons[self._current_topic]["code"]
        try:
            pyperclip.copy(code)
            self._status_label.setText("✅ Code copied to clipboard.")
        except Exception:
            self._status_label.setText(
                "⚠️ Couldn't copy to clipboard (xclip/xsel is probably not installed)."
            )

    # ---------------------------------------------------------------- Grading

    def check_answer(self):
        if not self._current_topic:
            return

        user_code = self._answer_input.toPlainText()
        if not user_code.strip():
            self._status_label.setText("⚠️ Write an answer first.")
            return

        self._check_button.setEnabled(False)
        self._status_label.setText("⏳ Running your code safely... (this takes a few seconds)")

        topic = self._current_topic
        self._worker = GradingWorker(topic, user_code)
        self._worker.finished.connect(
            lambda result: self._on_grading_finished(topic, user_code, result)
        )
        self._worker.start()

    def _on_grading_finished(self, topic: str, user_code: str, result: GradeResult):
        self._check_button.setEnabled(lessons[topic].get("auto_gradable", True))
        self._status_label.setText("")

        if result.infra_error:
            self._result_view.setPlainText(f"⚠️ Internal system error: {result.infra_error}")
            return

        # Record the attempt FIRST, before touching the sidebar or dashboard.
        # Refreshing the tree before this line was the bug: it would read
        # completed topics from the database before this attempt was saved,
        # so the checkmark only showed up after the *next* exercise was
        # checked (which triggered the following refresh, by which point
        # this attempt had already been recorded).
        record_attempt(DB_PATH, topic, result, code_length=len(user_code))

        if result.timed_out:
            self._result_view.setPlainText(
                "⏱️ Your code took too long to run (it might have an infinite loop)."
            )
            return

        if result.passed:
            self._result_view.setPlainText("✅ Nice! Your output was correct.")
            self._populate_tree()  # refresh checkmarks in the sidebar
        else:
            msg = "❌ Your answer isn't quite right yet.\n"
            if result.user_error:
                msg += f"\nRuntime error:\n{result.user_error}"
            elif result.diff_hint:
                msg += f"\n{result.diff_hint}"
            self._result_view.setPlainText(msg)


# ---------------------------------------------------------------- Main window

class ChatBotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Learning Chatbot")
        self.setGeometry(150, 80, 900, 650)

        init_db(DB_PATH)

        self._stack = QStackedWidget()
        self._dashboard_page = DashboardPage(on_start_learning=self.show_lesson_page)
        self._lesson_page = LessonPage(on_back_to_dashboard=self.show_dashboard_page)
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._lesson_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self.show_dashboard_page()

    def show_dashboard_page(self):
        self._dashboard_page.refresh()
        self._stack.setCurrentWidget(self._dashboard_page)

    def show_lesson_page(self):
        self._lesson_page.refresh()
        self._stack.setCurrentWidget(self._lesson_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = ChatBotApp()
    window.show()
    sys.exit(app.exec_())
