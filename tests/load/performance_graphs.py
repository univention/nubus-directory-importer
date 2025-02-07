# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

import pandas as pd

# Function to parse the log lines using string splits


def parse_simple_user_line(line):
    try:
        user_id = int(line.split("uid=user")[1].split(",ou=ad-sync")[0])
    except Exception:
        return {}
    return {"user_id": user_id}


def parse_user_line(line):
    try:
        user_id = int(line.split("uid=user_")[1].split("_")[1].split(",ou=ad-sync")[0])
    except Exception:
        return {}
    return {"user_id": user_id}


def parse_group_line(line):
    result = {}
    try:
        interim_group = line.split("_group-")[1].split(",ou=ad-sync")[0]

        result["group_number"], group_rest = interim_group.split("_max-members-")
        result["max_members"], result["group_instance"] = group_rest.split("_")
    except Exception:
        return {}
    return result


def create_dataframe(data):
    df = pd.DataFrame(data)
    df.sort_values(by="timestamp", inplace=True)
    df["time_delta"] = df["timestamp"].diff().dt.total_seconds()
    return df


def process_log_file(file_path, line_parser):
    lines = []

    with open(file_path, "r") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                timestamp = pd.Timestamp(line.split(" root[7]")[0])
            except Exception:
                print(f"failed to parse timestamp: {line_number}: {line}")
                continue

            parsed_line = line_parser(line)
            if parsed_line:
                lines.append({"timestamp": timestamp, **parsed_line})
            else:
                print(f"failed to parse line: {line_number}: {line}")

    # return create_dataframe(users), create_dataframe(groups)
    return create_dataframe(lines)


def group_stats(df):
    results = {}
    results["average"] = df["time_delta"].mean()
    results["average_10"] = df.loc[df["max_members"] == "10", "time_delta"].mean()
    results["average_1000"] = df.loc[df["max_members"] == "1000", "time_delta"].mean()
    return results


def remove_outliers(df, seconds):
    outliers = df[df["time_delta"] > seconds]
    print(f"found {len(outliers)} outliers:")
    print(outliers)
    return df.drop(outliers.index)
