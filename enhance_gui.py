#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图形界面：选择图片或文件夹与选项后调用 enhance_for_social.run。"""

from __future__ import annotations

import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from enhance_for_social import run

# 与「浏览文件」一致的常见图片后缀（小写比较）
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _default_output(input_path: Path) -> Path:
    stem = input_path.stem
    suffix = input_path.suffix or ".png"
    return input_path.with_name(f"{stem}_enhanced{suffix}")


def _list_images_in_folder(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    out: list[Path] = []
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            out.append(p)
    return sorted(out, key=lambda x: x.name.lower())


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Picture Beauty · 图片清晰化 / Mockup")
        self.minsize(560, 400)
        self.resizable(True, False)

        base = Path(__file__).resolve().parent
        default_in = base / "default.png"
        self._input_var = tk.StringVar(
            value=str(default_in) if default_in.is_file() else str(base)
        )
        self._output_var = tk.StringVar()
        self._preset_var = tk.StringVar(value="premium")
        self._canvas_var = tk.StringVar(value="mockup")
        self._card_style_var = tk.StringVar(value="shots")
        self._min_short_var = tk.StringVar(value="1080")

        self._cancel_event = threading.Event()
        self._worker: threading.Thread | None = None

        pad = {"padx": 10, "pady": 6}
        row = 0

        f_main = ttk.Frame(self, padding=12)
        f_main.pack(fill=tk.BOTH, expand=True)
        self._f_main = f_main

        ttk.Label(f_main, text="输入（文件或文件夹）").grid(row=row, column=0, sticky=tk.W, **pad)
        ent_in = ttk.Entry(f_main, textvariable=self._input_var, width=44)
        ent_in.grid(row=row, column=1, sticky=tk.EW, **pad)
        f_in_btn = ttk.Frame(f_main)
        f_in_btn.grid(row=row, column=2, **pad)
        ttk.Button(f_in_btn, text="选文件", width=8, command=self._browse_input_file).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(f_in_btn, text="选文件夹", width=8, command=self._browse_input_folder).pack(
            side=tk.LEFT
        )
        row += 1

        ttk.Label(f_main, text="输出").grid(row=row, column=0, sticky=tk.W, **pad)
        ent_out = ttk.Entry(f_main, textvariable=self._output_var, width=44)
        ent_out.grid(row=row, column=1, sticky=tk.EW, **pad)
        btn_out = ttk.Button(f_main, text="浏览输出…", command=self._browse_output)
        btn_out.grid(row=row, column=2, **pad)
        row += 1
        hint_lines = (
            "【选的是单张图片时】此处填「保存后的完整路径」（含文件名）；也可点「浏览输出…」选择保存位置。"
            "若留空：默认保存在原图同文件夹，文件名为「原文件名_enhanced」加原后缀。"
            "\n"
            "【选的是文件夹（批量）时】此处填「一个文件夹路径」，所有结果都保存到这个文件夹里；"
            "若留空：每张图各自保存在「该图片所在文件夹」，文件名同样是「原名_enhanced」。 "
            "（不含子文件夹，仅处理当前文件夹内的图片。）"
        )
        ttk.Label(
            f_main,
            text=hint_lines,
            foreground="gray",
            font=("TkDefaultFont", 8),
            wraplength=460,
            justify=tk.LEFT,
        ).grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=(10, 10), pady=(0, 8))
        row += 1

        ttk.Label(f_main, text="清晰度预设").grid(row=row, column=0, sticky=tk.W, **pad)
        f_preset = ttk.Frame(f_main)
        f_preset.grid(row=row, column=1, columnspan=2, sticky=tk.W, **pad)
        for val, lab in (
            ("premium", "平衡（推荐）"),
            ("light", "轻量"),
            ("strong", "更强"),
        ):
            ttk.Radiobutton(f_preset, text=lab, variable=self._preset_var, value=val).pack(
                side=tk.LEFT, padx=(0, 12)
            )
        row += 1

        ttk.Label(f_main, text="画布样式").grid(row=row, column=0, sticky=tk.NW, **pad)
        f_canvas = ttk.Frame(f_main)
        f_canvas.grid(row=row, column=1, columnspan=2, sticky=tk.W, **pad)
        canvas_opts = [
            ("mockup", "16:9 横版 Mockup（渐变+圆角+阴影）"),
            ("none", "仅清晰增强（无画框）"),
            ("xhs", "3:4 小红书"),
            ("douyin", "9:16 抖音竖屏"),
        ]
        for val, lab in canvas_opts:
            ttk.Radiobutton(
                f_canvas,
                text=lab,
                variable=self._canvas_var,
                value=val,
                command=self._sync_card_style_state,
            ).pack(anchor=tk.W, pady=2)
        row += 1

        ttk.Label(f_main, text="画框背景").grid(row=row, column=0, sticky=tk.W, **pad)
        f_card = ttk.Frame(f_main)
        f_card.grid(row=row, column=1, columnspan=2, sticky=tk.W, **pad)
        self._rb_shots = ttk.Radiobutton(
            f_card,
            text="Shots 风格（橙红→紫蓝对角渐变）",
            variable=self._card_style_var,
            value="shots",
        )
        self._rb_minimal = ttk.Radiobutton(
            f_card,
            text="深色竖渐变（简约）",
            variable=self._card_style_var,
            value="minimal",
        )
        self._rb_shots.pack(side=tk.LEFT, padx=(0, 12))
        self._rb_minimal.pack(side=tk.LEFT)
        row += 1

        ttk.Label(f_main, text="短边最小像素").grid(row=row, column=0, sticky=tk.W, **pad)
        f_short = ttk.Frame(f_main)
        f_short.grid(row=row, column=1, columnspan=2, sticky=tk.W, **pad)
        ent_short = ttk.Entry(f_short, textvariable=self._min_short_var, width=10)
        ent_short.pack(side=tk.LEFT)
        ttk.Label(f_short, text="（默认 1080，画质优先可调高）", foreground="gray").pack(
            side=tk.LEFT, padx=(8, 0)
        )
        row += 1

        f_main.columnconfigure(1, weight=1)

        self._status = tk.StringVar(value="就绪")
        ttk.Label(f_main, textvariable=self._status, foreground="gray").grid(
            row=row, column=0, columnspan=3, sticky=tk.W, padx=10, pady=(12, 4)
        )
        row += 1

        f_actions = ttk.Frame(f_main)
        f_actions.grid(row=row, column=1, columnspan=2, sticky=tk.E, pady=(8, 0))
        self._btn_run = ttk.Button(f_actions, text="开始处理", command=self._on_run)
        self._btn_run.pack(side=tk.LEFT, padx=(0, 8))
        self._btn_stop = ttk.Button(f_actions, text="停止", command=self._on_stop, state=tk.DISABLED)
        self._btn_stop.pack(side=tk.LEFT)
        self._f_actions = f_actions

        self._sync_card_style_state()

    def _set_busy(self, busy: bool) -> None:
        st = tk.DISABLED if busy else tk.NORMAL

        def walk(w: tk.Misc) -> None:
            if w == self._f_actions:
                return
            cls = w.winfo_class()
            if cls in ("TEntry", "TButton", "TRadiobutton"):
                try:
                    w.configure(state=st)
                except tk.TclError:
                    pass
            for c in w.winfo_children():
                walk(c)

        walk(self._f_main)
        self._btn_run.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self._btn_stop.configure(state=tk.NORMAL if busy else tk.DISABLED)
        if not busy:
            self._sync_card_style_state()

    def _worker_alive(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def _sync_card_style_state(self) -> None:
        on = self._canvas_var.get() != "none"
        state = tk.NORMAL if on else tk.DISABLED
        self._rb_shots.configure(state=state)
        self._rb_minimal.configure(state=state)

    def _browse_input_file(self) -> None:
        p = filedialog.askopenfilename(
            title="选择输入图片",
            filetypes=[
                ("图片", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif"),
                ("全部文件", "*.*"),
            ],
        )
        if p:
            self._input_var.set(p)
            if not self._output_var.get().strip():
                self._output_var.set(str(_default_output(Path(p))))

    def _browse_input_folder(self) -> None:
        p = filedialog.askdirectory(title="选择包含图片的文件夹（不递归子文件夹）")
        if p:
            self._input_var.set(p)
            self._output_var.set("")

    def _browse_output(self) -> None:
        inp = Path(self._input_var.get().strip())
        if inp.is_dir():
            p = filedialog.askdirectory(title="选择批量输出文件夹")
            if p:
                self._output_var.set(p)
            return
        p = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("全部", "*.*")],
            initialfile=Path(self._output_var.get() or self._input_var.get()).name,
        )
        if p:
            self._output_var.set(p)

    def _parse_min_short(self) -> int:
        s = self._min_short_var.get().strip()
        if not s.isdigit():
            raise ValueError("短边最小像素请填写正整数")
        v = int(s)
        if v < 256 or v > 8192:
            raise ValueError("短边像素建议在 256～8192 之间")
        return v

    def _build_jobs(self, inp: Path, out_spec: str) -> tuple[list[tuple[Path, Path]], str | None]:
        """
        返回 [(输入路径, 输出路径), ...]；若无法构建则第二个元素为错误说明。
        """
        out_spec = out_spec.strip()
        if inp.is_file():
            if not out_spec:
                return [(inp, _default_output(inp))], None
            outp = Path(out_spec)
            if outp.is_dir():
                suf = inp.suffix or ".png"
                return [(inp, outp / f"{inp.stem}_enhanced{suf}")], None
            outp.parent.mkdir(parents=True, exist_ok=True)
            return [(inp, outp)], None

        if inp.is_dir():
            files = _list_images_in_folder(inp)
            if not files:
                return [], f"文件夹内没有支持的图片：\n{inp}\n（后缀：{', '.join(sorted(IMAGE_EXTENSIONS))}，不含子文件夹）"
            jobs: list[tuple[Path, Path]] = []
            if not out_spec:
                for f in files:
                    jobs.append((f, _default_output(f)))
                return jobs, None
            root = Path(out_spec)
            if root.is_file():
                return [], "批量处理时，输出请填写文件夹路径，或留空以保存到各图片同目录。"
            try:
                root.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return [], f"无法创建或使用输出文件夹：{e}"
            for f in files:
                suf = f.suffix or ".png"
                jobs.append((f, root / f"{f.stem}_enhanced{suf}"))
            return jobs, None

        return [], f"路径不存在或不是文件/文件夹：\n{inp}"

    def _on_stop(self) -> None:
        self._cancel_event.set()
        self._status.set("正在停止…（当前这张处理完后不再继续）")

    def _finish_cancelled(self, completed: int, total: int) -> None:
        self._worker = None
        self._set_busy(False)
        self._status.set(f"已停止（已完成 {completed}/{total} 张）")
        messagebox.showinfo(
            "已停止",
            f"已完成 {completed} 张后停止。\n"
            "说明：若停止时正在处理某一张，该张会先处理完再结束；尚未开始的不会再跑。",
        )

    def _finish_ok(self, jobs: list[tuple[Path, Path]]) -> None:
        self._worker = None
        self._set_busy(False)
        total = len(jobs)
        if total == 1:
            self._status.set(f"完成 → {jobs[0][1]}")
            messagebox.showinfo("完成", f"已保存：\n{jobs[0][1]}")
            return
        roots = {str(d.parent) for _, d in jobs}
        where = "\n".join(sorted(roots))
        self._status.set(f"完成 {total} 张")
        messagebox.showinfo("完成", f"已处理 {total} 张图片。\n输出目录：\n{where}")

    def _finish_error(self, tb: str) -> None:
        self._worker = None
        self._set_busy(False)
        self._status.set("失败")
        messagebox.showerror("处理失败", tb)

    def _on_run(self) -> None:
        if self._worker_alive():
            return

        inp = Path(self._input_var.get().strip())
        try:
            min_short = self._parse_min_short()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return

        jobs, err = self._build_jobs(inp, self._output_var.get())
        if err:
            messagebox.showerror("错误", err)
            return
        if not jobs:
            messagebox.showerror("错误", "没有可处理的文件。")
            return

        canvas = self._canvas_var.get()
        mockup = canvas == "mockup"
        xhs = canvas == "xhs"
        douyin = canvas == "douyin"
        card_style = self._card_style_var.get() if canvas != "none" else "shots"
        preset = self._preset_var.get()

        total = len(jobs)
        self._cancel_event.clear()

        def task() -> None:
            completed = 0
            try:
                for i, (src, dst) in enumerate(jobs, start=1):
                    if self._cancel_event.is_set():
                        self.after(0, lambda c=completed, t=total: self._finish_cancelled(c, t))
                        return
                    self.after(
                        0,
                        lambda ii=i, name=src.name, tt=total: self._status.set(
                            f"处理中 {ii}/{tt}：{name}"
                        ),
                    )
                    run(
                        src,
                        dst,
                        preset=preset,
                        min_short=min_short,
                        mockup_169=mockup,
                        xhs_card=xhs,
                        douyin_card=douyin,
                        card_style=card_style,
                    )
                    completed += 1
                self.after(0, lambda j=list(jobs): self._finish_ok(j))
            except Exception:
                tb = traceback.format_exc()
                self.after(0, lambda msg=tb: self._finish_error(msg))

        self._set_busy(True)
        self._status.set(f"处理中 0/{total} …")
        self._worker = threading.Thread(target=task, daemon=True)
        self._worker.start()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
