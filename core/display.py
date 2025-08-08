"""
顯示美化模組
提供統一的終端輸出美化功能
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import os
import sys


@dataclass
class Colors:
    """ANSI 顏色碼"""
    # 基本顏色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 亮色版本
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # 樣式
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    STRIKETHROUGH = '\033[9m'
    
    # 重置
    RESET = '\033[0m'
    
    @classmethod
    def disable(cls):
        """停用顏色（用於不支援的終端）"""
        for attr in dir(cls):
            if not attr.startswith('_') and attr.isupper():
                setattr(cls, attr, '')


@dataclass 
class Symbols:
    """Unicode 符號"""
    # 狀態符號
    CHECK = '✓'
    CROSS = '✗'
    WARNING = '⚠'
    INFO = 'ℹ'
    STAR = '★'
    ARROW = '→'
    BULLET = '•'
    
    # 進度符號
    PROGRESS_EMPTY = '○'
    PROGRESS_FULL = '●'
    
    # 方框符號
    BOX_TOP_LEFT = '┌'
    BOX_TOP_RIGHT = '┐'
    BOX_BOTTOM_LEFT = '└'
    BOX_BOTTOM_RIGHT = '┘'
    BOX_HORIZONTAL = '─'
    BOX_VERTICAL = '│'
    BOX_CROSS = '┼'
    BOX_T_DOWN = '┬'
    BOX_T_UP = '┴'
    BOX_T_RIGHT = '├'
    BOX_T_LEFT = '┤'
    
    # 分隔線
    LINE_THIN = '─' * 50
    LINE_THICK = '═' * 50
    LINE_DOUBLE = '━' * 50
    LINE_DOTTED = '┈' * 50
    LINE_DASHED = '┅' * 50


class Display:
    """統一的顯示管理器"""
    
    def __init__(self, use_color: bool = True, width: int = 70):
        """
        初始化顯示管理器
        
        Args:
            use_color: 是否使用顏色
            width: 顯示寬度
        """
        self.colors = Colors()
        self.symbols = Symbols()
        self.width = width
        
        if not use_color or not self._supports_color():
            Colors.disable()
    
    def _supports_color(self) -> bool:
        """檢查終端是否支援顏色"""
        # Windows 需要特殊處理
        if sys.platform == 'win32':
            return os.environ.get('ANSICON') is not None
        # Unix-like 系統
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def clear_screen(self):
        """清空螢幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def header(self, title: str, subtitle: Optional[str] = None):
        """顯示標題頭"""
        print()
        print(f"{self.colors.CYAN}{self.symbols.LINE_DOUBLE}{self.colors.RESET}")
        print(f"{self.colors.BOLD}{self.colors.CYAN}  {title}{self.colors.RESET}")
        if subtitle:
            print(f"{self.colors.DIM}  {subtitle}{self.colors.RESET}")
        print(f"{self.colors.CYAN}{self.symbols.LINE_DOUBLE}{self.colors.RESET}")
        print()
    
    def section(self, title: str, icon: str = ""):
        """顯示區段標題"""
        icon_str = f"{icon} " if icon else ""
        print()
        print(f"{self.colors.YELLOW}{icon_str}{self.colors.BOLD}{title}{self.colors.RESET}")
        print(f"{self.colors.DIM}{self.symbols.LINE_THIN}{self.colors.RESET}")
    
    def success(self, message: str):
        """顯示成功訊息"""
        print(f"{self.colors.GREEN}{self.symbols.CHECK} {message}{self.colors.RESET}")
    
    def error(self, message: str):
        """顯示錯誤訊息"""
        print(f"{self.colors.RED}{self.symbols.CROSS} {message}{self.colors.RESET}")
    
    def warning(self, message: str):
        """顯示警告訊息"""
        print(f"{self.colors.YELLOW}{self.symbols.WARNING} {message}{self.colors.RESET}")
    
    def info(self, message: str):
        """顯示資訊訊息"""
        print(f"{self.colors.BLUE}{self.symbols.INFO} {message}{self.colors.RESET}")
    
    def item(self, label: str, value: str, color: Optional[str] = None):
        """顯示標籤值對"""
        value_color = getattr(self.colors, color.upper()) if color else ""
        reset = self.colors.RESET if color else ""
        print(f"  {self.colors.DIM}{label}:{self.colors.RESET} {value_color}{value}{reset}")
    
    def list_item(self, text: str, level: int = 0, symbol: Optional[str] = None):
        """顯示列表項目"""
        indent = "  " * level
        symbol = symbol or self.symbols.BULLET
        print(f"{indent}{self.colors.DIM}{symbol}{self.colors.RESET} {text}")
    
    def progress_bar(self, current: int, total: int, label: str = "", width: int = 30):
        """顯示進度條"""
        percentage = current / total if total > 0 else 0
        filled = int(width * percentage)
        empty = width - filled
        
        bar = (
            f"{self.colors.GREEN}{'█' * filled}{self.colors.RESET}"
            f"{self.colors.DIM}{'░' * empty}{self.colors.RESET}"
        )
        
        percentage_str = f"{percentage * 100:.1f}%"
        
        if label:
            print(f"  {label}: {bar} {percentage_str}")
        else:
            print(f"  {bar} {percentage_str}")
    
    def box(self, title: str, content: List[str], color: Optional[str] = None):
        """顯示方框內容"""
        box_color = getattr(self.colors, color.upper()) if color else self.colors.DIM
        
        # 計算最大寬度
        max_width = max(len(title), max(len(line) for line in content)) + 4
        
        # 上邊框
        print(f"{box_color}{self.symbols.BOX_TOP_LEFT}{'─' * (max_width - 2)}{self.symbols.BOX_TOP_RIGHT}{self.colors.RESET}")
        
        # 標題
        padding = max_width - len(title) - 4
        print(f"{box_color}{self.symbols.BOX_VERTICAL}{self.colors.RESET} {self.colors.BOLD}{title}{self.colors.RESET}{' ' * padding} {box_color}{self.symbols.BOX_VERTICAL}{self.colors.RESET}")
        
        # 分隔線
        print(f"{box_color}{self.symbols.BOX_T_RIGHT}{'─' * (max_width - 2)}{self.symbols.BOX_T_LEFT}{self.colors.RESET}")
        
        # 內容
        for line in content:
            padding = max_width - len(line) - 4
            print(f"{box_color}{self.symbols.BOX_VERTICAL}{self.colors.RESET} {line}{' ' * padding} {box_color}{self.symbols.BOX_VERTICAL}{self.colors.RESET}")
        
        # 下邊框
        print(f"{box_color}{self.symbols.BOX_BOTTOM_LEFT}{'─' * (max_width - 2)}{self.symbols.BOX_BOTTOM_RIGHT}{self.colors.RESET}")
    
    def table(self, headers: List[str], rows: List[List[str]], colors: Optional[List[str]] = None):
        """顯示表格"""
        # 計算每列的最大寬度
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)
        
        # 顯示標題
        header_line = ""
        for i, header in enumerate(headers):
            header_line += f"{self.colors.BOLD}{header.ljust(col_widths[i])}{self.colors.RESET}"
        print(header_line)
        
        # 分隔線
        print(self.colors.DIM + "─" * sum(col_widths) + self.colors.RESET)
        
        # 顯示資料行
        for row in rows:
            row_line = ""
            for i, cell in enumerate(row):
                if colors and i < len(colors):
                    color = getattr(self.colors, colors[i].upper(), "")
                    row_line += f"{color}{str(cell).ljust(col_widths[i])}{self.colors.RESET}"
                else:
                    row_line += str(cell).ljust(col_widths[i])
            print(row_line)
    
    def collapsible(self, title: str, content: str, expanded: bool = False):
        """顯示可折疊內容（模擬）"""
        if expanded:
            print(f"{self.colors.BLUE}▼ {title}{self.colors.RESET}")
            for line in content.split('\n'):
                print(f"  {self.colors.DIM}{line}{self.colors.RESET}")
        else:
            print(f"{self.colors.BLUE}▶ {title}{self.colors.RESET} {self.colors.DIM}(詳細內容已折疊){self.colors.RESET}")
    
    def separator(self, style: str = "thin"):
        """顯示分隔線"""
        styles = {
            "thin": self.symbols.LINE_THIN,
            "thick": self.symbols.LINE_THICK,
            "double": self.symbols.LINE_DOUBLE,
            "dotted": self.symbols.LINE_DOTTED,
            "dashed": self.symbols.LINE_DASHED
        }
        line = styles.get(style, self.symbols.LINE_THIN)
        print(f"{self.colors.DIM}{line}{self.colors.RESET}")
    
    def blank_line(self, count: int = 1):
        """插入空行"""
        for _ in range(count):
            print()


# 建立全域顯示實例
display = Display()


# 便捷函數
def print_header(title: str, subtitle: Optional[str] = None):
    """顯示標題頭"""
    display.header(title, subtitle)


def print_success(message: str):
    """顯示成功訊息"""
    display.success(message)


def print_error(message: str):
    """顯示錯誤訊息"""
    display.error(message)


def print_warning(message: str):
    """顯示警告訊息"""
    display.warning(message)


def print_info(message: str):
    """顯示資訊訊息"""
    display.info(message)