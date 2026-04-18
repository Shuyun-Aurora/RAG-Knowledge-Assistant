import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import logging
from lib.lightrag.mineru_parser import MineruParser
from repository.llm_repository import QwenVision, encode_image_to_base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil


class DocumentParserRepository:
    def __init__(self, qwen_api_key: str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger.addHandler(handler)
        self.qwen_vision = QwenVision(qwen_api_key)

    def parse_document(
        self,
        file_content: bytes,
        filename: str,
        output_dir: str = "./output",
        parse_method: str = "auto",
        display_stats: bool = True,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        使用MinerU解析文档
        
        Args:
            file_content: 文件内容
            filename: 文件名
            output_dir: 输出目录
            parse_method: 解析方法
            display_stats: 是否显示统计信息
            
        Returns:
            (content_list, md_content): 内容列表和markdown文本
        """
        self.logger.info(f"开始解析文档: {filename}")
        
        # 创建临时文件
        temp_dir = Path(output_dir) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / filename
        
        try:
            # 写入临时文件
            with open(temp_file_path, "wb") as f:
                f.write(file_content)
            
            # 根据文件扩展名选择解析方法
            ext = Path(filename).suffix.lower()
            file_stem = Path(filename).stem
            method = parse_method
            if ext in [".pdf"]:
                self.logger.info(f"检测到PDF文件，使用PDF解析器 (method={parse_method})...")
                content_list, md_content = MineruParser.parse_pdf(
                    pdf_path=temp_file_path, output_dir=output_dir, method=parse_method
                )
                # import os
                # import mineru.utils.models_download_utils as mdu
                # from mineru.cli import client

                # # === 环境变量配置 ===
                # os.environ.update({
                #     "MINERU_MODEL_DIR": "/root/mineru",
                #     "MINERU_DISABLE_MULTIPROCESS": "1",
                #     "MINERU_TELEMETRY_DISABLE": "1",
                #     "MINERU_VERBOSE": "true",
                #     "MINERU_LOG_LEVEL": "DEBUG",
                #     "TOKENIZERS_PARALLELISM": "false",
                #     "OMP_NUM_THREADS": "1",
                #     "OPENBLAS_NUM_THREADS": "1",
                #     "MKL_NUM_THREADS": "1",
                #     "NUMEXPR_NUM_THREADS": "1",
                # })

                # def patched_auto_download_and_get_model_root_path(model_enum):
                #     model_dir = os.getenv("MINERU_MODEL_DIR")
                #     if not model_dir:
                #         raise RuntimeError("MINERU_MODEL_DIR not set, please export it before running mineru")
                #     return model_dir

                # mdu.auto_download_and_get_model_root_path = patched_auto_download_and_get_model_root_path

                # # === 调用 MinerU CLI 主函数 ===
                # client.main(
                #     args=[
                #         "-p", str(temp_file_path),
                #         "-o", str(output_dir),
                #         "-m", "auto",    
                #         "-b", "pipeline",     
                #         "--source", "local"
                #     ]
                # )
                # self.logger.info("MinerU CLI 解析完成。")
                
            elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"]:
                self.logger.info("检测到图片文件，使用图片解析器...")
                content_list, md_content = MineruParser.parse_image(
                    image_path=temp_file_path, output_dir=output_dir
                )
                method = "ocr"
            elif ext in [".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"]:
                self.logger.info("检测到Office文档，使用Office解析器...")
                content_list, md_content = MineruParser.parse_office_doc(
                    doc_path=temp_file_path, output_dir=output_dir
                )
            else:
                self.logger.info(f"使用通用解析器处理 {ext} 文件 (method={parse_method})...")
                content_list, md_content = MineruParser.parse_document(
                    file_path=temp_file_path, method=parse_method, output_dir=output_dir
                )

            # 搬运文件，消除多余嵌套
            target_dir = Path(output_dir) 
            nested_dir = target_dir / file_stem / method
            if nested_dir.exists() and nested_dir.is_dir():
                for item in nested_dir.iterdir():
                    shutil.move(str(item), str(target_dir))
                try:
                    nested_dir.rmdir()
                    (target_dir / file_stem).rmdir()
                except Exception as e:
                    self.logger.warning(f"清理嵌套目录失败: {e}")

        except Exception as e:
            self.logger.error(f"特定解析器出错: {str(e)}")
            self.logger.warning("回退到通用解析器...")
            content_list, md_content = MineruParser.parse_document(
                file_path=temp_file_path, method=parse_method, output_dir=output_dir
            )
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()
        
        self.logger.info(f"解析完成！提取了 {len(content_list)} 个内容块")
        self.logger.info(f"Markdown文本长度: {len(md_content)} 字符")
        
        # 显示内容统计信息
        if display_stats:
            self._display_content_stats(content_list, md_content)
        
        return content_list, md_content

    def _display_content_stats(self, content_list: List[Dict[str, Any]], md_content: str) -> None:
        """显示内容统计信息"""
        self.logger.info("\n内容信息:")
        self.logger.info(f"* 内容块总数: {len(content_list)}")
        self.logger.info(f"* Markdown内容长度: {len(md_content)} 字符")

    def process_text(self, item: Dict[str, Any], page_idx: int) -> str:
        """处理文本内容"""
        text = item.get('text', '')
        if not text.strip():
            return ""
        return text

    def process_image(self, item: Dict[str, Any], page_idx: int, output_dir: Path) -> str:
        """处理图片内容"""
        image_path = output_dir / item.get('img_path', '')
        
        if not image_path or not os.path.exists(image_path):
            self.logger.warning(f"[第{page_idx}页][图片] 无法获取本地图片路径，跳过")
            return ""
        
        try:
            image_data_url = encode_image_to_base64(str(image_path))
            desc = self.qwen_vision.analyze_image(image_data_url, "image")
            self.logger.info(f"[第{page_idx}页][图片] 分析完成: {desc[:30]}...")
            return desc
        except Exception as e:
            self.logger.error(f"[第{page_idx}页][图片] Qwen-VL分析失败: {e}")
            return ""

    def process_table(self, item: Dict[str, Any], page_idx: int, output_dir: Path) -> str:
        """处理表格内容"""
        image_path = output_dir / item.get('img_path', '')
        
        if not image_path or not os.path.exists(image_path):
            self.logger.warning(f"[第{page_idx}页][表格] 无法获取本地图片路径，跳过")
            return ""
        
        try:
            image_data_url = encode_image_to_base64(str(image_path))
            desc = self.qwen_vision.analyze_image(image_data_url, "table")
            self.logger.info(f"[第{page_idx}页][表格] 分析完成: {desc[:30]}...")
            return desc
        except Exception as e:
            self.logger.error(f"[第{page_idx}页][表格] Qwen-VL分析失败: {e}")
            return ""

    def process_equation(self, item: Dict[str, Any], page_idx: int, output_dir: Path) -> str:
        """处理公式内容"""
        image_path = output_dir / item.get('img_path', '')
        
        if not image_path or not os.path.exists(image_path):
            print(image_path)
            self.logger.warning(f"[第{page_idx}页][公式] 无法获取本地图片路径，跳过")
            return ""
        
        try:
            image_data_url = encode_image_to_base64(str(image_path))
            desc = self.qwen_vision.analyze_image(image_data_url, "equation")
            self.logger.info(f"[第{page_idx}页][公式] 分析完成: {desc[:30]}...")
            return desc
        except Exception as e:
            self.logger.error(f"[第{page_idx}页][公式] Qwen-VL分析失败: {e}")
            return ""

    # def process_content_by_order(self, content_list: List[Dict[str, Any]], output_dir: Path) -> Tuple[List[Dict[str, Any]], str]:
    #     """
    #     页间并行，页内图片/表格/公式并发，text顺序，最终顺序和原文件一致。
    #     同一页的内容合并为一个chunk。
    #     返回每个chunk的文本和其覆盖的所有page_idx列表（page_indices），以及用于知识图谱的纯文本。
    #     """
    #     # 1. 按 page_idx 分组，记录原始索引
    #     page_map = defaultdict(list)
    #     for idx, item in enumerate(content_list):
    #         page_idx = item.get("page_idx", -1)
    #         page_map[page_idx].append((idx, item))  # (原始索引, item)

    #     def process_one_page(page_idx, items):
    #         # items: List[(原始索引, item)]
    #         results = [None] * len(items)
    #         with ThreadPoolExecutor() as inner_executor:
    #             futures = {}
    #             for i, (orig_idx, item) in enumerate(items):
    #                 t = item.get("type", "unknown")
    #                 if t == "text":
    #                     results[i] = {"text": self.process_text(item, page_idx), "page_indices": [page_idx], "type": "text"}
    #                 elif t == "image":
    #                     futures[inner_executor.submit(self.process_image, item, page_idx, output_dir)] = i
    #                 elif t == "table":
    #                     futures[inner_executor.submit(self.process_table, item, page_idx, output_dir)] = i
    #                 elif t == "equation":
    #                     futures[inner_executor.submit(self.process_equation, item, page_idx, output_dir)] = i
    #                 else:
    #                     self.logger.warning(f"[第{page_idx}页][未知类型] {t}")
    #             for future in as_completed(futures):
    #                 i = futures[future]
    #                 try:
    #                     results[i] = {"text": future.result(), "page_indices": [page_idx], "type": "image"}
    #                 except Exception as e:
    #                     results[i] = {"text": "", "page_indices": [page_idx], "type": "image"}
    #         # 保证顺序
    #         blocks = [r for r in results if r and r["text"]]
    #         return page_idx, blocks

    #     # 页间并行
    #     results = {}
    #     with ThreadPoolExecutor() as executor:
    #         future_to_page = {
    #             executor.submit(process_one_page, page_idx, items): page_idx
    #             for page_idx, items in page_map.items()
    #         }
    #         for future in as_completed(future_to_page):
    #             page_idx, blocks = future.result()
    #             results[page_idx] = blocks

    #     # 按原顺序合并，每页合成一个chunk
    #     all_blocks = []
    #     kg_text_blocks = []  # 用于知识图谱的纯文本块
        
    #     for page_idx in sorted(results.keys()):
    #         page_blocks = results[page_idx]
    #         if page_blocks:
    #             merged_text = "\n\n".join([b["text"] for b in page_blocks if b["text"]])
    #             if merged_text.strip():
    #                 all_blocks.append({"text": merged_text, "page_indices": [page_idx]})
                    
    #                 # 只将纯文本内容添加到知识图谱文本中
    #                 text_only_blocks = [b for b in page_blocks if b.get("type") == "text" and b["text"].strip()]
    #                 if text_only_blocks:
    #                     text_only_text = "\n\n".join([b["text"] for b in text_only_blocks])
    #                     if text_only_text.strip():
    #                         kg_text_blocks.append(text_only_text)
        
    #     # 拼接所有纯文本内容用于知识图谱生成
    #     kg_text = "\n\n".join(kg_text_blocks)
        
    #     return all_blocks, kg_text 

    def process_content_by_order(self, content_list: List[Dict[str, Any]], output_dir: Path) -> Tuple[List[Dict[str, Any]], str]:
        """
        无任何并发
        """
        from collections import defaultdict

        # 1. 按 page_idx 分组
        page_map = defaultdict(list)
        for idx, item in enumerate(content_list):
            page_idx = item.get("page_idx", -1)
            page_map[page_idx].append((idx, item))  # (原始索引, item)

        def process_one_page(page_idx, items):
            """处理单页：页内完全串行"""
            results = []
            for orig_idx, item in items:
                t = item.get("type", "unknown")
                text = ""

                if t == "text":
                    text = self.process_text(item, page_idx)
                elif t == "image":
                    text = self.process_image(item, page_idx, output_dir)
                elif t == "table":
                    text = self.process_table(item, page_idx, output_dir)
                elif t == "equation":
                    text = self.process_equation(item, page_idx, output_dir)
                else:
                    self.logger.warning(f"[第{page_idx}页][未知类型] {t}")

                if text:
                    results.append({"text": text, "page_indices": [page_idx], "type": t})

            return page_idx, results

        # ✅ 页间串行处理
        results = {}
        for page_idx in sorted(page_map.keys()):
            _, blocks = process_one_page(page_idx, page_map[page_idx])
            results[page_idx] = blocks

        # 按原顺序合并，每页合成一个chunk
        all_blocks = []
        kg_text_blocks = []

        for page_idx in sorted(results.keys()):
            page_blocks = results[page_idx]
            if page_blocks:
                merged_text = "\n\n".join([b["text"] for b in page_blocks if b["text"]])
                if merged_text.strip():
                    all_blocks.append({"text": merged_text, "page_indices": [page_idx]})

                    # 只将纯文本内容添加到知识图谱文本中
                    text_only_blocks = [b for b in page_blocks if b.get("type") == "text" and b["text"].strip()]
                    if text_only_blocks:
                        text_only_text = "\n\n".join([b["text"] for b in text_only_blocks])
                        if text_only_text.strip():
                            kg_text_blocks.append(text_only_text)

        # 拼接所有纯文本内容用于知识图谱生成
        kg_text = "\n\n".join(kg_text_blocks)

        return all_blocks, kg_text
