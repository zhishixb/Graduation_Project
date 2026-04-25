from typing import List, Dict, Any


class CommentParser:
    """解析小红书单篇笔记评论数据，提取 note_id 和所有评论内容及点赞数"""

    @staticmethod
    def parse(comments_data: List[Dict], note_id: str) -> List[Dict[str, Any]]:
        """
        将单篇笔记的评论数据扁平化

        :param comments_data: crawl_comments 返回的评论列表
        :param note_id: 所属笔记 ID
        :return: 扁平化评论列表，每个元素包含 note_id, content, like_count
        """
        result = []
        CommentParser._extract_comments(comments_data, note_id, result)
        return result

    @staticmethod
    def _extract_comments(comments: List[Dict], note_id: str, result: List[Dict]) -> None:
        """
        递归提取评论和子评论，将它们添加到结果列表中

        :param comments: 评论列表
        :param note_id: 所属笔记 ID
        :param result: 累积结果的列表
        """
        for comment in comments:
            content = comment.get('content', '')
            like_count = comment.get('like_count', '0')

            result.append({
                'note_id': note_id,
                'content': content,
                'like_count': like_count
            })

            # 处理子评论
            sub_comments = comment.get('sub_comments', [])
            if sub_comments:
                CommentParser._extract_comments(sub_comments, note_id, result)