from openai import OpenAI
from langchain.embeddings.base import Embeddings


class QwenEmbeddings(Embeddings):
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def embed_documents(self, texts):
        all_embeddings = []
        for i in range(0, len(texts), 10):
            batch = texts[i:i + 10]
            response = self.client.embeddings.create(
                model="text-embedding-v4",
                input=batch,
                dimensions=1024,
                encoding_format="float"
            )
            all_embeddings.extend([e.embedding for e in response.data])
        return all_embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]
