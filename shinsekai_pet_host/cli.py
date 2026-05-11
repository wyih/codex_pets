from __future__ import annotations

import argparse
from pathlib import Path
import sys

from shinsekai_pet_host.backends import BackendConfig, BackendProviderRegistry
from shinsekai_pet_host.codex_cli import CodexAuthService
from shinsekai_pet_host.persona import compose_pet_prompt
from shinsekai_pet_host.petpack import PetPack, PetRegistry, validate_petpack


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PET_ROOTS = [ROOT / "pets", Path.home() / ".codex" / "shinsekai-pets"]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    pets = PetRegistry(DEFAULT_PET_ROOTS).discover()
    if args.command == "list":
        return cmd_list(pets)
    if args.command == "validate":
        return cmd_validate(pets)
    if args.command == "auth":
        return cmd_auth(args)
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "desktop":
        from shinsekai_pet_host.desktop_preview import main as desktop_main

        return desktop_main()
    if args.command == "chat":
        return cmd_chat(args, pets)
    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shinsekai Pet Host prototype")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="List discovered PetPacks")
    sub.add_parser("validate", help="Validate discovered PetPacks")
    auth = sub.add_parser("auth", help="Show Codex CLI login status")
    auth.add_argument("--codex-bin", default="codex")
    sub.add_parser("doctor", help="Check optional desktop Qt/PySide setup")
    sub.add_parser("desktop", help="Open the optional PySide desktop host")
    chat = sub.add_parser("chat", help="Send a message through a backend")
    chat.add_argument("message")
    chat.add_argument("--pet", default="anaxa-sage")
    chat.add_argument("--mode", choices=["chat", "work"], default="chat")
    chat.add_argument("--workspace", default="")
    chat.add_argument("--backend", choices=BackendProviderRegistry.default().ids(), default="codex-cli")
    chat.add_argument("--model", default="")
    chat.add_argument("--endpoint", default="")
    chat.add_argument("--api-key", default="")
    chat.add_argument("--codex-bin", default="codex")
    chat.add_argument("--timeout", type=int, default=120)
    return parser


def cmd_list(pets: list[PetPack]) -> int:
    for pet in pets:
        print(f"{pet.manifest.id}\t{pet.manifest.display_name}\t{pet.manifest.asset_format}")
    return 0


def cmd_validate(pets: list[PetPack]) -> int:
    failures = 0
    for pet in pets:
        report = validate_petpack(pet)
        if report.ok:
            print(f"ok\t{pet.manifest.id}")
            continue
        failures += 1
        for message in report.messages:
            print(f"fail\t{message}", file=sys.stderr)
    if failures:
        return 1
    print(f"{len(pets)} pet(s) ok")
    return 0


def cmd_auth(args: argparse.Namespace) -> int:
    status = CodexAuthService(codex_bin=args.codex_bin).status()
    print(status.message)
    return 0 if status.ok else 1


def cmd_doctor() -> int:
    from shinsekai_pet_host.qt_doctor import run_qt_doctor

    result = run_qt_doctor()
    for line in result.lines:
        print(line)
    return 0 if result.ok else 1


def cmd_chat(args: argparse.Namespace, pets: list[PetPack]) -> int:
    pet = _select_pet(pets, args.pet)
    if pet is None:
        print(f"unknown pet: {args.pet}", file=sys.stderr)
        return 2
    config = BackendConfig(
        provider=args.backend,
        model=args.model,
        endpoint=args.endpoint,
        api_key=args.api_key,
        command=args.codex_bin,
        timeout_seconds=args.timeout,
    )
    backend = BackendProviderRegistry.default().create(config)
    prompt = compose_pet_prompt(pet, args.message, mode=args.mode)
    result = backend.send(prompt, mode=args.mode, workspace=args.workspace)
    if result.text:
        print(result.text)
    if not result.ok:
        print(result.error, file=sys.stderr)
        return 1
    return 0


def _select_pet(pets: list[PetPack], pet_id: str) -> PetPack | None:
    for pet in pets:
        if pet.manifest.id == pet_id:
            return pet
    return None


if __name__ == "__main__":
    raise SystemExit(main())
