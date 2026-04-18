from pathlib import Path
from lib.lightrag.mineru_parser import MineruParser
from repository.llm_repository import QwenVision
from repository.embedding_repository import QwenEmbeddings
import os
import base64

class DocumentParserService:
    def __init__(self, embedding_repo, vision_repo, vector_dao):
        self.embedding_repo = embedding_repo
        self.vision_repo = vision_repo
        self.vector_dao = vector_dao

    def encode_image_to_base64(self, image_path: str) -> str:
        ext = os.path.splitext(image_path)[-1].lower()
        mime = "image/jpeg"
        if ext == ".png":
            mime = "image/png"
        elif ext == ".gif":
            mime = "image/gif"
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"

    def parse_and_store(self, file_path, course_name):
        # 1. 解析文档
        content_list, _ = MineruParser.parse_document(file_path, output_dir="./output")
        output_dir = Path("./output") / Path(file_path).stem / "auto"
        for item in content_list:
            page_idx = item.get("page_idx", -1)
            t = item.get("type", "unknown")
            if t == "text":
                text = item.get('text', '')
                if not text.strip():
                    continue
                emb = self.embedding_repo.embed_documents([text])[0]
                self.vector_dao.add([text], [{"type": "text", "page": page_idx, "course": course_name}])
            elif t in ["image", "table", "equation"]:
                image_path = output_dir / item.get('img_path', '')
                if not image_path or not os.path.exists(image_path):
                    continue
                image_data_url = self.encode_image_to_base64(str(image_path))
                desc = self.vision_repo.analyze_image(image_data_url, t)
                emb = self.embedding_repo.embed_documents([desc])[0]
                self.vector_dao.add([desc], [{"type": t, "page": page_idx, "img_path": str(image_path), "course": course_name}])
        self.vector_dao.save() 