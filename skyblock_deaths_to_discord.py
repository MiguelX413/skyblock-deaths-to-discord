#!/usr/bin/env python3
import logging
import time
from typing import List

import requests
from discord_webhook import DiscordWebhook


def connect_sub_clauses(sub_clauses: List[str]) -> str:
    if len(sub_clauses) == 0:
        return ""
    elif len(sub_clauses) == 1:
        return sub_clauses[0]
    elif len(sub_clauses) == 2:
        return f"{sub_clauses[0]} and {sub_clauses[1]}"
    else:
        return f"{', '.join(sub_clauses[:-1])}, and {sub_clauses[-1]}"


def send_message(
    webhook: DiscordWebhook,
    username: str,
    hypixel_api_key: str,
    player_uuid: str,
    min_deaths: int = 1,
    tags: List[str] = None,
) -> None:
    data = requests.get(
        url="https://api.hypixel.net/skyblock/profiles",
        params={"key": hypixel_api_key, "uuid": player_uuid},
    ).json()
    webhook.content = "".join(
        [
            username,
            " has died ",
            connect_sub_clauses(
                list(
                    f"{int(profile['members'][player_uuid.replace('-', '')]['stats'].get('deaths', 0))!s} times on profile {profile['cute_name']}"
                    for profile in filter(
                        lambda profile: int(
                            profile["members"][player_uuid.replace("-", "")][
                                "stats"
                            ].get("deaths", 0)
                        )
                        >= min_deaths,
                        data["profiles"],
                    )
                )
            ),
            f"\n{' '.join(tags)}" if tags is not None else "",
        ]
    )
    webhook.execute()


def message_loop(
    webhook_url: str,
    hypixel_api_key: str,
    player_uuid: str,
    frequency: float = 3600.0,
    min_deaths: int = 1,
    tags: List[str] = None,
) -> None:
    start_time = time.time()
    username: str = requests.get(
        url="https://api.hypixel.net/player",
        params={"key": hypixel_api_key, "uuid": player_uuid},
    ).json()["player"]["playername"]
    discord_webhook = DiscordWebhook(
        url=webhook_url, rate_limit_retry=True, username=f"{username} death tracker"
    )
    while True:
        send_message(
            discord_webhook, username, hypixel_api_key, player_uuid, min_deaths, tags
        )
        time.sleep(frequency - ((time.time() - start_time) % frequency))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Use debug logging")
    parser.add_argument(
        "webhook_url", action="store", type=str, help="Discord Webhook URL"
    )
    parser.add_argument(
        "hypixel_api_key", action="store", type=str, help="Hypixel API key"
    )
    parser.add_argument("player_uuid", action="store", type=str, help="Player UUID")
    parser.add_argument(
        "-f",
        "--frequency",
        action="store",
        type=float,
        help="The amount of seconds between messages",
        default=3600.0,
    )
    parser.add_argument(
        "-m",
        "--min-deaths",
        action="store",
        type=int,
        help="The minimum amount of deaths",
        default=1,
    )
    parser.add_argument(
        "-t", "--tags", action="append", type=str, help="Tags to tag in messages"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logging.info(args)

    message_loop(
        args.webhook_url,
        args.hypixel_api_key,
        args.player_uuid,
        args.frequency,
        args.min_deaths,
        args.tags,
    )


if __name__ == "__main__":
    main()
