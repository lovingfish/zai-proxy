import base64
import io
import httpx
from typing import Optional, Dict, Any
from api.config import get_settings
from api.logger import setup_logger

logger = setup_logger(__name__)


class ImageUploader:
    """图片上传工具类，支持 base64 图片上传"""

    def __init__(self, access_token: str):
        """
        初始化图片上传器

        Args:
            access_token: 认证令牌
        """
        self.settings = get_settings()
        self.access_token = access_token
        self.upload_url = f"{self.settings.PROXY_URL}/api/v1/files/"

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://chat.z.ai",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "authorization": f"Bearer {self.access_token}",
        }
        return headers

    async def upload_base64_image(
        self, base64_data: str, filename: Optional[str] = None
    ) -> Optional[str]:
        """
        上传 base64 编码的图片

        Args:
            base64_data: base64 编码的图片数据（不包含 data:image/...;base64, 前缀）
            filename: 可选的文件名，如果不提供将自动生成

        Returns:
            上传成功返回图片 URL，失败返回 None
        """
        try:
            # 如果没有提供文件名，生成一个默认文件名
            if not filename:
                import time

                filename = f"pasted_image_{int(time.time() * 1000)}.png"

            # 解码 base64 数据
            try:
                image_data = base64.b64decode(base64_data)
            except Exception as e:
                logger.error(f"Base64 解码失败: {e}")
                return None

            # 创建文件对象
            file_obj = io.BytesIO(image_data)

            # 准备 multipart/form-data
            files = {"file": (filename, file_obj, "image/png")}

            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.upload_url,
                    headers=self._get_headers(),
                    files=files,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                # 提取 图片id
                cdn_url = result.get("meta", {}).get("cdn_url")
                pic_id = result.get("id")
                if cdn_url:
                    logger.info(f"图片上传成功: {filename}")
                    return pic_id
                else:
                    logger.error("上传响应中未找到 CDN URL")
                    return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            return None

    async def upload_image_from_url(self, image_url: str) -> Optional[str]:
        """
        从 URL 下载图片并上传

        Args:
            image_url: 图片 URL

        Returns:
            上传成功返回新的图片 URL，失败返回 None
        """
        try:
            # 下载图片
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30.0)
                response.raise_for_status()

                # 获取文件名
                filename = image_url.split("/")[-1]
                if not filename or "." not in filename:
                    import time

                    filename = f"downloaded_image_{int(time.time() * 1000)}.png"

                # 编码为 base64
                base64_data = base64.b64encode(response.content).decode("utf-8")

                # 上传图片
                return await self.upload_base64_image(base64_data, filename)

        except Exception as e:
            logger.error(f"从 URL 上传图片失败: {e}")
            return None
