
def patch_dispatcher_for_testing(dispatcher_class):
    """
    为 IBKRDispatcher 注入 get_all_results 方法，方便单元测试中查看内部数据。
    """
    def get_all_results(self):
        return {k: list(v) for k, v in self._results.items()}

    setattr(dispatcher_class, 'get_all_results', get_all_results)
