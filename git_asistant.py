#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import signal
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def ensure_dependencies(requirements_file: str = "requirements.txt") -> None:
    """
    Garantiza que las dependencias de requirements.txt están instaladas.
    - Ejecuta: pip install -r requirements.txt
    - Reintenta con --user si falla por permisos.
    - Sale con código 1 si no puede instalarlas.
    """
    req = Path(requirements_file).expanduser().resolve()
    if not req.exists():
        print(f"[deps] No se encontró {req}. Si no quieres dependencias, crea un requirements.txt vacío.")
        return

    # Primer intento: instalación normal en el intérprete actual
    print(f"[deps] Verificando dependencias con {req}...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    proc = subprocess.run(cmd, text=True, capture_output=True)

    if proc.returncode != 0:
        print("[deps] Falló la instalación estándar. Intento con --user (permisos de usuario).")
        cmd_user = [sys.executable, "-m", "pip", "install", "--user", "-r", str(req)]
        proc_user = subprocess.run(cmd_user, text=True, capture_output=True)

        if proc_user.returncode != 0:
            # Muestra algo útil y aborta
            print("====================================")
            print("[deps] ERROR: No se pudieron instalar las dependencias.")
            print("-------- stdout --------")
            print(proc.stdout or "")
            print(proc_user.stdout or "")
            print("-------- stderr --------")
            print(proc.stderr or "")
            print(proc_user.stderr or "")
            print("====================================")
            print("Sugerencias:")
            print(f"1) Prueba manualmente: {sys.executable} -m pip install -r {req}")
            print("2) Si es tema de permisos, usa un entorno virtual (venv) o --user.")
            sys.exit(1)
    else:
        # Instalación correcta o ya satisfechas
        print("[deps] Dependencias instaladas correctamente o ya satisfechas.")

ensure_dependencies("requirements.txt")

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from rich import box
from rich.text import Text

console = Console(highlight=False)

# Dependencias interactivas
try:
    from InquirerPy import inquirer
    from InquirerPy.separator import Separator
except Exception as e:
    console.print("[bold red]Falta la librería InquirerPy.[/bold red] Instala con: [yellow]pip install InquirerPy[/yellow]")
    sys.exit(1)

# YAML opcional
try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # lo manejamos a mano

# Estado global para revertir si hay Ctrl+C
TOUCHED_REPOS: List[Path] = []
FILES_ADDED_BY_REPO: Dict[str, List[str]] = {}  # repo_path -> files staged (para revertir)
BRANCH_CHANGED: Dict[str, Tuple[str, str]] = {}  # repo_path -> (old_branch, new_branch)


def run_git(repo: Path, args: List[str], check: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta comando git en repo, imprime output en vivo, devuelve el CompletedProcess."""
    cmd = ["git"] + args
    with console.status(f"[bold cyan]git {' '.join(args)}[/bold cyan] en [magenta]{repo}[/magenta]"):
        proc = subprocess.run(cmd, cwd=str(repo), text=True, capture_output=True)
    # Mostrar salida formateada
    if proc.stdout.strip():
        console.print(Panel(proc.stdout.strip(), title="stdout", border_style="green"))
    if proc.stderr.strip():
        console.print(Panel(proc.stderr.strip(), title="stderr", border_style="red"))
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falló con código {proc.returncode}")
    return proc


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def load_projects(file_path: Path) -> List[Dict[str, str]]:
    if not file_path.exists():
        console.print(f"[red]No existe el fichero: {file_path}[/red]")
        sys.exit(1)

    ext = file_path.suffix.lower()
    try:
        if ext in [".json"]:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        elif ext in [".yaml", ".yml"]:
            if yaml is None:
                console.print("[yellow]El archivo es YAML pero no tienes PyYAML instalado. Instálalo con[/yellow] [cyan]pip install pyyaml[/cyan].")
                sys.exit(1)
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        else:
            console.print("[red]Formato no soportado. Usa .json o .yaml (.yml).[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error leyendo {file_path}: {e}[/red]")
        sys.exit(1)

    # Validar estructura
    projects = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or "name" not in item or "path" not in item:
            console.print(f"[red]Elemento #{i} inválido. Debe tener 'name' y 'path'.[/red]")
            sys.exit(1)
        projects.append({"name": str(item["name"]), "path": str(item["path"])})
    return projects


def choose_projects(projects: List[Dict[str, str]]) -> List[Dict[str, str]]:
    choices = [Separator("— Selecciona proyectos con ESPACIO —")] + [
        {"name": f"{p['name']}  [dim]{p['path']}[/dim]", "value": p} for p in projects
    ]
    sel = inquirer.checkbox(
        message="¿Qué proyectos quieres actualizar?",
        choices=choices,
        instruction="ESPACIO para marcar, ENTER para confirmar",
        cycle=True,
        validate=lambda r: len(r) > 0 or "Selecciona al menos uno o cancela",
        invalid_message="Selecciona al menos un proyecto."
    ).execute()

    if not sel:
        if Confirm.ask("No hay selección. ¿Cancelar?", default=True):
            sys.exit(0)
    return sel


def browse_and_select_files(repo_path: Path) -> List[str]:
    """
    Navegación por carpetas con selector simple.
    Devuelve rutas RELATIVAS al repo.
    """
    current = repo_path
    selected: List[Path] = []
    visited_files: set = set()

    while True:
        table = Table(box=box.SIMPLE, title=f"[bold]Explorando[/bold] [cyan]{current}[/cyan]")
        table.add_column("Índice", style="magenta", justify="right", no_wrap=True)
        table.add_column("Tipo", style="yellow", no_wrap=True)
        table.add_column("Nombre", style="white")
        entries = []

        # Controles especiales
        controls = []
        if current != repo_path:
            controls.append(("..", "[Subir]", current.parent))
        controls.append(("[Terminar selección]", "[OK]", None))
        # Listar directorios y archivos
        try:
            dir_entries = sorted(list(current.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            console.print("[red]Sin permisos para listar este directorio.[/red]")
            dir_entries = []

        idx = 1
        index_map = {}
        # Controles primero
        for label, typ, target in controls:
            table.add_row(str(idx), typ, label)
            index_map[idx] = ("control", target, label)
            idx += 1

        # Directorios
        for d in [p for p in dir_entries if p.is_dir()]:
            table.add_row(str(idx), "dir", d.name + "/")
            index_map[idx] = ("dir", d, d.name)
            idx += 1
        # Archivos
        for f in [p for p in dir_entries if p.is_file()]:
            mark = " [green](seleccionado)[/green]" if f in selected else ""
            table.add_row(str(idx), "file", f.name + mark)
            index_map[idx] = ("file", f, f.name)
            idx += 1

        console.print(table)
        choice = Prompt.ask("Elige índice (o 'b' borrar, 'l' listar selección)", default="")
        if not choice:
            continue
        
        if choice.strip() == "¡":
            ai_panel()

        if choice.lower() == "l":
            if selected:
                console.print("\n[bold]Archivos seleccionados hasta ahora:[/bold]")
                for i, f in enumerate(selected, 1):
                    console.print(f"  {i}. {f.relative_to(repo_path)}")
            else:
                console.print("[dim]No hay archivos seleccionados todavía.[/dim]")
            input("Pulsa Enter para continuar...")
            continue

        if choice.lower() == "b":
            if selected:
                removed = selected.pop()
                console.print(f"[yellow]Quitado[/yellow] {removed.relative_to(repo_path)}")
            else:
                console.print("[dim]No hay nada que quitar.[/dim]")
            continue

        try:
            num = int(choice)
        except ValueError:
            console.print("[red]Entrada no válida.[/red]")
            continue

        if num not in index_map:
            console.print("[red]Índice fuera de rango.[/red]")
            continue

        kind, target, label = index_map[num]
        if kind == "control":
            if label == "..":
                current = target  # type: ignore
            else:
                # [Terminar selección]
                if not selected:
                    if Confirm.ask("No has seleccionado ningún archivo. ¿Terminar igualmente?", default=False):
                        return []
                    else:
                        continue
                console.print("\n[bold]Selección final:[/bold]")
                for i, f in enumerate(selected, 1):
                    console.print(f"  {i}. {f.relative_to(repo_path)}")
                if Confirm.ask("¿Confirmar y salir?", default=True):
                    return [str(p.relative_to(repo_path)) for p in selected]
                else:
                    continue

        elif kind == "dir":
            current = target  # type: ignore

        elif kind == "file":
            fpath: Path = target  # type: ignore
            if fpath in selected:
                console.print("[dim]Ya estaba seleccionado.[/dim]")
            else:
                selected.append(fpath)
                visited_files.add(str(fpath))
                console.print(
                    f"[green]Añadido[/green] {fpath.relative_to(repo_path)} "
                    f"([cyan]{len(selected)} seleccionados[/cyan])"
                )


def show_selected(selected: List[Path], base: Path) -> None:
    if not selected:
        console.print("[dim]Sin archivos seleccionados.[/dim]")
        return
    table = Table(title="Seleccionados", box=box.SIMPLE)
    table.add_column("#", justify="right", style="magenta")
    table.add_column("Archivo", style="white")
    for i, p in enumerate(selected, 1):
        table.add_row(str(i), str(p.relative_to(base)))
    console.print(table)


def ensure_clean_repo(repo: Path) -> None:
    if not is_git_repo(repo):
        console.print(f"[yellow]{repo} no es un repositorio git.[/yellow]")
        if Confirm.ask("¿Quieres inicializar un nuevo repositorio aquí?", default=True):
            run_git(repo, ["init"], check=True)
            console.print(f"[green]Repositorio inicializado en {repo}[/green]")

            # Preguntar por remote
            if Confirm.ask("¿Quieres configurar un remoto (origin)?", default=True):
                remote_url = Prompt.ask("URL del remoto (ej. git@github.com:usuario/repo.git)").strip()
                if remote_url:
                    run_git(repo, ["remote", "add", "origin", remote_url], check=True)
                    console.print(f"[green]Remote 'origin' configurado a {remote_url}[/green]")

            # Preguntar por rama inicial
            default_branch = Prompt.ask("Nombre de la rama inicial", default="main").strip()
            if default_branch:
                run_git(repo, ["checkout", "-b", default_branch], check=True)
                console.print(f"[green]Rama inicial '{default_branch}' creada[/green]")

        else:
            console.print("[red]Operación cancelada, no es un repositorio git.[/red]")
            sys.exit(1)


def get_branches(repo: Path) -> Tuple[str, List[str]]:
    # rama actual
    cur = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    # ramas locales
    loc = run_git(repo, ["branch", "--format", "%(refname:short)"]).stdout.strip().splitlines()
    return cur, [b.strip() for b in loc if b.strip()]


def checkout_branch(repo: Path, branch: str, create: bool = False) -> None:
    if create:
        run_git(repo, ["checkout", "-b", branch], check=True)
    else:
        run_git(repo, ["checkout", branch], check=True)


def ask_branch_flow(repo: Path) -> str:
    current, branches = get_branches(repo)

    console.print(Panel(f"Rama actual: [bold green]{current}[/bold green]", title="Ramas", border_style="cyan"))
    action = inquirer.select(
        message="¿Usar rama existente o crear nueva?",
        choices=[
            {"name": "Usar rama existente", "value": "existing"},
            {"name": "Crear nueva rama", "value": "new"},
        ],
        default="existing",
    ).execute()

    if action == "existing":
        if not branches:
            console.print("[yellow]No hay ramas locales. Crearé una nueva.[/yellow]")
            action = "new"
        else:
            choice = inquirer.select(
                message="Selecciona rama",
                choices=branches,
                default=current if current in branches else branches[0],
                cycle=True,
            ).execute()
            if choice != current:
                BRANCH_CHANGED[str(repo)] = (current, choice)
                checkout_branch(repo, choice, create=False)
            return choice

    # Crear nueva
    new_name = Prompt.ask("Nombre de la nueva rama").strip()
    if not new_name:
        console.print("[red]Nombre de rama vacío.[/red]")
        sys.exit(1)
    BRANCH_CHANGED[str(repo)] = (current, new_name)
    checkout_branch(repo, new_name, create=True)
    return new_name


def add_and_commit(repo: Path, add_all: bool, files: Optional[List[str]]) -> None:
    global TOUCHED_REPOS, FILES_ADDED_BY_REPO
    TOUCHED_REPOS.append(repo)

    if add_all:
        run_git(repo, ["add", "."], check=True)
        FILES_ADDED_BY_REPO.setdefault(str(repo), []).append(".")
    else:
        if not files:
            console.print("[yellow]No se proporcionaron archivos. Nada que añadir.[/yellow]")
            return
        # Validar existencia
        ok = []
        for f in files:
            if (repo / f).exists():
                ok.append(f)
            else:
                console.print(f"[red]No existe:[/red] {f}")
        if ok:
            run_git(repo, ["add"] + ok, check=True)
            FILES_ADDED_BY_REPO.setdefault(str(repo), []).extend(ok)
        else:
            console.print("[yellow]No hay archivos válidos para añadir.[/yellow]")

    # commit
    msg = Prompt.ask("Nombre del commit").strip()
    if not msg:
        console.print("[red]Mensaje vacío. Cancelando commit.[/red]")
        return
    cp = run_git(repo, ["commit", "-m", msg])
    if cp.returncode != 0:
        console.print("[yellow]Puede que no hubiera cambios que commitear.[/yellow]")

def has_uncommitted_changes(repo: Path) -> bool:
    cp = run_git(repo, ["status", "--porcelain"])
    return bool(cp.stdout.strip())

def maybe_stage_and_commit(repo: Path) -> None:
    """Si hay cambios sin commit, enseña los cambios y pregunta si quieres añadirlos/committear."""
    if not has_uncommitted_changes(repo):
        console.print("[dim]No hay cambios sin commitear.[/dim]")
        return

    # Mostrar qué cambios hay (git status --short)
    status = run_git(repo, ["status", "--short"])
    if status.stdout.strip():
        console.print(Panel(status.stdout.strip(), title="Cambios detectados", border_style="cyan"))

    if not Confirm.ask("¿Quieres añadir estos ficheros antes de hacer push?", default=True):
        console.print("[yellow]No se añadirán cambios. El push solo enviará lo ya commiteado.[/yellow]")
        return

    # Flujo de selección
    include_all = Confirm.ask("¿Incluir todos los ficheros con 'git add .'?", default=True)
    files = None
    if not include_all:
        files = []
        while True:
            picked = browse_and_select_files(repo)
            for p in picked:
                if p not in files:
                    files.append(p)
            if not Confirm.ask("¿Añadir más archivos?", default=False):
                break

    add_and_commit(repo, include_all, files)


def ask_action() -> str:
    return inquirer.select(
        message="¿Qué quieres hacer ahora?",
        choices=[
            Separator("— Sincronizar / Inspeccionar —"),
            "Pull",
            "Fetch",
            "Status",
            "Log (últimos 10)",
            Separator("— Publicar / Ramas —"),
            "Push directo (origin HEAD)",
            "Push y establecer upstream (origin <branch>)",
            "Crear Pull Request (requiere GitHub CLI 'gh')",
            "Cambiar/crear rama",
            "Nada, salir",
        ],
        default="Status",
        cycle=True,
    ).execute()


def do_action(repo: Path, action: str) -> None:
    # Rama actual por si hace falta
    current_branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()

    if action == "Pull":
        run_git(repo, ["pull", "--ff-only"], check=False)
    elif action == "Fetch":
        run_git(repo, ["fetch", "--all", "--prune"], check=False)
    elif action == "Status":
        run_git(repo, ["status"], check=False)
    elif action == "Log (últimos 10)":
        run_git(repo, ["log", "--oneline", "-10", "--graph", "--decorate"], check=False)
    elif action.startswith("Push directo"):
        run_git(repo, ["push", "origin", "HEAD"], check=False)
    elif action.startswith("Push y establecer upstream"):
        run_git(repo, ["push", "-u", "origin", current_branch], check=False)
    elif action.startswith("Crear Pull Request"):
        gh = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if gh.returncode != 0:
            console.print("[yellow]No tienes la GitHub CLI 'gh' instalada o configurada.[/yellow]")
            console.print("Instala desde https://cli.github.com/ y ejecuta [cyan]gh auth login[/cyan].")
            return
        title = Prompt.ask("Título del PR", default=f"Actualizaciones en {current_branch}")
        body = Prompt.ask("Descripción del PR", default="Actualización automática desde asistente.")
        base = Prompt.ask("Rama base (a la que apuntas)", default="main")
        res = subprocess.run(
            ["gh", "pr", "create", "--base", base, "--head", current_branch, "--title", title, "--body", body],
            cwd=str(repo), text=True, capture_output=True
        )
        if res.stdout.strip():
            console.print(Panel(res.stdout.strip(), title="gh stdout", border_style="green"))
        if res.stderr.strip():
            console.print(Panel(res.stderr.strip(), title="gh stderr", border_style="red"))
        if res.returncode != 0:
            console.print("[red]Fallo creando el PR.[/red]")
        else:
            console.print("[green]Pull Request creado correctamente.[/green]")
    elif action == "Cambiar/crear rama":
        ask_branch_flow(repo)



def revert_changes():
    """Revertir lo que se haya tocado en los repos si hay Ctrl+C."""
    for repo in TOUCHED_REPOS:
        try:
            console.print(Panel(f"Revirtiendo cambios en [magenta]{repo}[/magenta]...", border_style="yellow"))
            # Deshacer stage
            run_git(repo, ["restore", "--staged", "."], check=False)
            # Resetear working tree a HEAD
            run_git(repo, ["reset", "--hard"], check=False)
            # Limpiar untracked
            run_git(repo, ["clean", "-fd"], check=False)
            # Volver a rama anterior si cambió
            if str(repo) in BRANCH_CHANGED:
                old, new = BRANCH_CHANGED[str(repo)]
                run_git(repo, ["checkout", old], check=False)
        except Exception:
            pass


def handle_sigint(signum, frame):
    console.print("\n[bold red]Saliendo del programa... revirtiendo cambios... una pena[/bold red]")
    try:
        revert_changes()
    finally:
        sys.exit(130)


def main():
    signal.signal(signal.SIGINT, handle_sigint)

    console.print(Panel("Asistente Git de Consola", subtitle="Por Rubén Núñez Cotano",
                        border_style="cyan", title="[bold]🚀[/bold]"))

    # Pedir fichero de proyectos
    default_file = "proyectos.json"
    file_path_str = Prompt.ask("¿Cuál es tu fichero de configuración (por defecto proyectos.json)?", default=default_file)
    file_path = Path(file_path_str).expanduser().resolve()

    projects = load_projects(file_path)
    if not projects:
        console.print("[red]No hay proyectos en el fichero.[/red]")
        sys.exit(1)

    selected = choose_projects(projects)

    # Por cada proyecto, flujo de add/commit/branch/acciones
    for proj in selected:
        name = proj["name"]
        path = Path(proj["path"]).expanduser().resolve()

        console.print(Panel(Text(f"{name}\n{path}", justify="left"),
                            title="Proyecto", border_style="magenta"))

        ensure_clean_repo(path)

        while True:
            action = ask_action()
            if action == "Nada, salir":
                break

            # Para acciones de publicar (push/PR), ofrece add/commit SOLO si hay cambios
            if action.startswith("Push") or action.startswith("Crear Pull Request"):
                maybe_stage_and_commit(path)

            # Para cambiar/crear rama, se gestiona dentro de do_action
            do_action(path, action)

            if not Confirm.ask("¿Hacer otra acción en este repo?", default=False):
                break


        console.print(Panel("[bold green]Todo listo.[/bold green] ¡Hasta la próxima!", border_style="green"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Por si acaso
        handle_sigint(None, None)
