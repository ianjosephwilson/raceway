raceway
#########

Minimal dependency injection, DI, system ideal for smaller systems that still need DI.

Overview
--------

  - Defining: Define protocols and implementations.
  - Loading: Load registrations extracted from implementations into planner.
  - Starting: Run startup to create container from planner.
  - Wrapping: Use injector to wrap task handlers to prepare for injection.
  - Running: Create task for each "runner" and use it with the container to execute each injection enabled task handler.

Example
-------

This library is meant to be used with an external framework but this example
uses python's stdlib threading to demonstrate how the pieces fit together.

.. code-block:: python

    import threading
    import time
    from dataclasses import dataclass
    from typing import Protocol
    from random import random

    from raceway.extractor import configure_extractor
    from raceway.registration import Registration
    from raceway.planner import configure_planner
    from raceway.starter import startup
    from raceway.injector import configure_injector
    from raceway.protocols import IContainer, ITask, IInjector, IExtractor

    class ICrawlJob(ITask, Protocol):
        def get_link(self) -> str: ...

    @dataclass
    class CrawlJob(ICrawlJob):
        def __hash__(self):
            return id(self)
        def __eq__(self, other: object):
            return self is other
        id: int
        link: str
        def get_link(self) -> str:
            return self.link

    class ICrawler(Protocol):
        def crawl(self, delay: float) -> str: ...

    @dataclass
    class CrawlerService(ICrawler):
        job: ICrawlJob
        def crawl(self, delay: float) -> str:
            return f"Crawled {self.job.get_link()} in {delay}s."

    def run_job(crawler_api: ICrawler) -> None:
        delay = 3*random()
        time.sleep(delay)  # Blocking I/O (simulating a network request)
        print (crawler_api.crawl(delay))


    def main():
        #
        # Setup
        #
        extractor_api =  configure_extractor()
        injector_api = configure_injector(extractor=extractor_api, task_proto=ICrawlJob)
        planner = configure_planner(task_proto=ICrawlJob)
        planner.queue_registration(
            ICrawler,
            Registration(
                CrawlerService, extractor_api.extract(CrawlerService), scope="task"
            ),
        )
        container_api = startup(planner=planner)

        # Prepare job runner for injection.
        wrapped_with_inject = injector_api.wrap_in_inject(run_job)

        #
        # Payloads
        #
        links = [
            "https://python.org",
            "https://docs.python.org",
            "https://peps.python.org",
            *[f"https://example.com/{v}" for v in range(20)],
        ]


        #
        # Start threads for each link
        #
        threads = []
        for link_id, link in enumerate(links):
            # Using `args` to pass positional arguments and `kwargs` for keyword arguments
            # ... in our case we are passing the args the inject function will need.
            job = CrawlJob(link_id, link)
            t = threading.Thread(
                target=wrapped_with_inject,
                args=(container_api, job),
            )
            threads.append(t)

        # Start each thread
        for t in threads:
            t.start()

        # Wait for all threads to finish
        for t in threads:
            t.join()


    if __name__ == '__main__':
        main()
