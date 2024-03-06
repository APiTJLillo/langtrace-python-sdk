from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from src.init import init
from src.utils.with_root_span import with_langtrace_root_span

_ = load_dotenv(find_dotenv())

init(batch=True, log_spans_to_console=True, write_to_remote_url=False)

client = OpenAI()


@with_langtrace_root_span()
def images_generate():
    result = client.images.generate(
        model="dall-e-3",
        prompt="A cute baby sea otter",
    )
    print(result)
