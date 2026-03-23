import os


def main() -> int:
    model = os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini')
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('OPENAI_API_KEY not set')
        return 2

    messages = [
        {"role": "system", "content": "You are a concise test assistant."},
        {"role": "user", "content": "Send a short confirmation message: Hello from the Jupyter integration test."}
    ]

    # Keep this as an explicit manual smoke test instead of a pytest import-time side effect.
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(model=model, messages=messages)
        content = None
        if hasattr(resp, 'choices') and len(resp.choices) > 0:
            choice = resp.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                content = choice.message.content
            elif isinstance(choice, dict) and 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
        if content is None:
            content = resp['choices'][0]['message']['content']
        print('Assistant:', content)
        return 0
    except Exception as new_error:
        try:
            import openai
            openai.api_key = api_key
            resp = openai.ChatCompletion.create(model=model, messages=messages)
            content = resp['choices'][0]['message']['content']
            print('Assistant:', content)
            return 0
        except Exception as legacy_error:
            print('Both client attempts failed.')
            print('New client error:', repr(new_error))
            print('Legacy client error:', repr(legacy_error))
            return 3


if __name__ == '__main__':
    raise SystemExit(main())
