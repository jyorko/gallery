from typing import Literal

import sema4ai_http
from microsoft_teams.models import (
    GetChannelMessagesRequest,
    GetMessageRepliesRequest,
    TeamSearchRequest,
    UserSearch,
)
from microsoft_teams.support import (
    BASE_GRAPH_URL,
    build_headers,
    parse_channel_messages,
    parse_message_replies,
)
from sema4ai.actions import ActionError, OAuth2Secret, Response, action


@action
def get_joined_teams(
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["Team.ReadBasic.All"]],
    ],
) -> Response[dict]:
    """
    Get all Teams the user is joined to with the full details. Can be used to search Teams as well.

    Args:
        token: OAuth2 token to use for the operation.

    Returns:
        Result of the operation
    """
    headers = build_headers(token)
    response = sema4ai_http.get(
        f"{BASE_GRAPH_URL}/me/joinedTeams",
        headers=headers,
    )
    if response.status_code in [200, 201]:
        return Response(result=response.json())
    else:
        raise ActionError(f"Failed to get joined teams: {response.text}")


@action
def search_team_by_name(
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["Group.Read.All"]],
    ],
    search_request: TeamSearchRequest,
) -> Response[list[dict]]:
    """
    Search for a Microsoft Team by its name.

    Args:
        token: OAuth2 token to use for the operation.
        search_request: Pydantic model containing the team name to search for.

    Returns:
        Result of the search operation, including details of matching teams.
    """
    headers = build_headers(token)
    team_name = search_request.team_name

    response = sema4ai_http.get(
        f"{BASE_GRAPH_URL}/groups?$filter=displayName eq '{team_name}' and resourceProvisioningOptions/Any(x:x eq 'Team')",
        headers=headers,
    )

    if response.status_code in [200, 201]:
        teams = response.json().get("value", [])
        return Response(result=teams)
    else:
        raise ActionError(f"Failed to search for team: {response.text}")


@action
def get_team_members(
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["TeamMember.Read.All"]],
    ],
    team_id: str,
) -> Response[dict]:
    """
    Get the members of a specific Microsoft Team.

    Args:
        token: OAuth2 token to use for the operation.
        team_id: The ID of the Microsoft Team.

    Returns:
        Result of the operation
    """
    if not team_id:
        raise ActionError("The team_id must be provided")

    headers = build_headers(token)
    response = sema4ai_http.get(
        f"{BASE_GRAPH_URL}/teams/{team_id}/members",
        headers=headers,
    )
    if response.status_code in [200, 201]:
        return Response(result=response.json())
    else:
        raise ActionError(f"Failed to get team members: {response.text}")


@action
def get_team_channels(
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["Channel.ReadBasic.All"]],
    ],
    team_id: str,
) -> Response[dict]:
    """
    Get the channels of a specific Microsoft Team.

    Args:
        token: OAuth2 token to use for the operation.
        team_id: The ID of the Microsoft Team.

    Returns:
        Result of the operation
    """
    if not team_id:
        raise ActionError("The team_id must be provided")

    headers = build_headers(token)
    response = sema4ai_http.get(
        f"{BASE_GRAPH_URL}/teams/{team_id}/channels",
        headers=headers,
    )
    if response.status_code in [200, 201]:
        return Response(result=response.json())
    else:
        raise ActionError(f"Failed to get team channels: {response.text}")


@action
def search_user(
    user_search: UserSearch,
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["User.Read.All"]],
    ],
) -> Response[list[dict]]:
    """
    Search for a user by email, first name, or last name.

    Args:
        user_search: The search criteria (email, first name, or last name).
        token: OAuth2 token to use for the operation.

    Returns:
        Result of the operation with user details if found.
    """
    headers = build_headers(token)
    search_query = []
    if user_search.email:
        search_query.append(f"mail eq '{user_search.email}'")
    if user_search.first_name:
        search_query.append(f"startswith(givenName,'{user_search.first_name}')")
    if user_search.last_name:
        search_query.append(f"startswith(surname,'{user_search.last_name}')")

    filter_query = " and ".join(search_query)
    response = sema4ai_http.get(
        f"{BASE_GRAPH_URL}/users?$filter={filter_query}",
        headers=headers,
    )

    if response.status_code in [200, 201]:
        search_results = response.json().get("value", [])
        return Response(result=search_results)
    else:
        raise ActionError(f"Failed to search for user: {response.text}")


@action
def get_channel_messages(
    messages_request: GetChannelMessagesRequest,
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["ChannelMessage.Read.All"]],
    ],
) -> Response[dict]:
    """
    Get messages from a specific channel in a Microsoft Team. Message replies not included but you can use "get_message_replies" if needed.

    Args:
        messages_request: Pydantic model containing the team ID, channel ID, and an limit for the number of messages to retrieve. Use 10 if not specified.
        token: OAuth2 token to use for the operation.

    Returns:
        Result of the operation.
    """
    headers = build_headers(token)

    team_id = messages_request.team_id
    channel_id = messages_request.channel_id
    limit = messages_request.limit

    url = f"https://graph.microsoft.com/beta/teams/{team_id}/channels/{channel_id}/messages?$top={limit}"

    response = sema4ai_http.get(url, headers=headers)

    if response.status_code in [200, 201]:
        parsed_data = parse_channel_messages(response.json())
        return Response(result={"messages": parsed_data})
    else:
        raise ActionError(f"Failed to get channel messages: {response.text}")


@action
def get_message_replies(
    replies_request: GetMessageRepliesRequest,
    token: OAuth2Secret[
        Literal["microsoft"],
        list[Literal["ChannelMessage.Read.All"]],
    ],
) -> Response[dict]:
    """
    Get replies to a specific message in a Microsoft Team channel.

    Args:
        replies_request: Pydantic model containing the team ID, channel ID, and message ID.
        token: OAuth2 token to use for the operation.

    Returns:
        Result of the operation, including a list of parsed replies if successful.
    """
    headers = build_headers(token)

    team_id = replies_request.team_id
    channel_id = replies_request.channel_id
    message_id = replies_request.message_id

    url = f"https://graph.microsoft.com/beta/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies"

    response = sema4ai_http.get(url, headers=headers)

    if response.status_code in [200, 201]:
        parsed_data = parse_message_replies(response.json())
        return Response(result={"replies": parsed_data})
    else:
        raise ActionError(f"Failed to get message replies: {response.text}")
