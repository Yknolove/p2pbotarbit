"""
Referral system handlers for the ArbitPro bot.

This module implements the invite/referral logic using plain JSON files to
record invitations and grant PRO status when enough friends sign up.  It
fixes a bug in the original implementation where the aiogram handler used
``regexp_command`` for injection, which is not supported in aiogram v3.
Instead we annotate the handler with the ``regexp`` parameter typed as
``re.Match[str]``.
"""

import json
import re
from aiogram import Router, F
from aiogram.types import Message


router = Router()
REF_FILE = "referrals.json"
PRO_USERS_FILE = "pro_users.json"


def load_json(filename: str):
    """Load a JSON file and return its contents or an empty dict on error."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(filename: str, data) -> None:
    """Serialize ``data`` to ``filename`` with indentation for readability."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


@router.message(F.text == "/refer")
async def send_ref_link(message: Message) -> None:
    """Send a personal referral link to the user."""
    ref_code = f"ref{message.chat.id}"
    link = f"https://t.me/ArbitProBot?start={ref_code}"
    await message.answer(
        "👥 Пригласи друзей и получи 3 дня PRO!\n\n"
        "Вот твоя ссылка:\n"
        f"{link}"
    )


@router.message(F.text == "/myref")
async def show_ref_stats(message: Message) -> None:
    """Display referral statistics for the current user."""
    ref_data = load_json(REF_FILE).get(str(message.chat.id), {})
    count = len(ref_data.get("invited", []))
    used = ref_data.get("used_bonus", False)
    await message.answer(
        f"👥 Приглашено: {count} пользователей\n"
        f"🎁 Бонус использован: {'✅ Да' if used else '❌ Нет'}"
    )


@router.message(F.text.regexp(r"^/start ref(\d+)$"))
async def register_referral(message: Message, regexp: re.Match[str]) -> None:
    """Register a new user as invited by another user's referral link.

    The handler uses a regular expression to capture the inviter's chat ID
    from the ``/start`` command.  If the user tries to invite themselves or
    has already been invited by the same person, appropriate messages are
    returned.  Once two users have been invited successfully, the inviter
    receives PRO status for a limited time.

    Args:
        message: The incoming aiogram Message.
        regexp: A regex match object containing the inviter's ID as group 1.
    """
    inviter_id = regexp.group(1)
    user_id = str(message.chat.id)

    # Disallow self‑invites
    if user_id == inviter_id:
        await message.answer("❗ Нельзя пригласить самого себя.")
        return

    refs = load_json(REF_FILE)
    invited_by_inviter = refs.get(inviter_id, {}).get("invited", [])
    if user_id in invited_by_inviter:
        await message.answer("✅ Вы уже были приглашены этим пользователем.")
        return

    # Create record for inviter if necessary
    if inviter_id not in refs:
        refs[inviter_id] = {"invited": [], "used_bonus": False}
    refs[inviter_id]["invited"].append(user_id)

    # Grant bonus if conditions met
    if len(refs[inviter_id]["invited"]) >= 2 and not refs[inviter_id]["used_bonus"]:
        pro = load_json(PRO_USERS_FILE)
        if "users" not in pro:
            pro["users"] = []
        if inviter_id not in pro["users"]:
            pro["users"].append(inviter_id)
        refs[inviter_id]["used_bonus"] = True
        save_json(PRO_USERS_FILE, pro)

    save_json(REF_FILE, refs)
    await message.answer("🎉 Вы были успешно зарегистрированы как приглашённый!")