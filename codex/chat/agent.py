import codex.common.ai_model


async def start_chat(ids, app, request):
    """
    Create a new chat for a given application and user.
    """
    ai = codex.common.ai_model.OpenAIChatClient.get_instance()
    ans = await ai.chat(
        {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant called codex. Your job is to guide the users through the creation of a software product",
                },
                {"role": "user", "content": request.message},
            ],
        }
    )
    return ans.choices[0].message.content


async def continue_chat(ids, app, request):
    """
    Keep working through the interview until it is finished
    """
    return "Chat continued successfully"
