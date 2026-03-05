class Comment:
    __slots__ = (
        'comment_id', 'weibo_id', 'user_id', 'username',
        'content', 'publish_time', 'up_num'
    )

    def to_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot)}

    def __init__(self):
        self.comment_id = ''
        self.weibo_id = ''
        self.user_id = ''
        self.username = ''
        self.content = ''
        self.publish_time = ''
        self.up_num = 0
