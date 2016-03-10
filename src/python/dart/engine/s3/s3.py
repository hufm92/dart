import logging
import os
import traceback

from dart.client.python.dart_client import Dart
from dart.engine.s3.actions.copy import s3_copy
from dart.engine.s3.metadata import S3ActionTypes
from dart.model.engine import ActionResultState, ActionResult
from dart.tool.tool_runner import Tool

_logger = logging.getLogger(__name__)


class S3Engine(object):
    def __init__(self, dart_host, dart_port, dart_api_version):
        self.dart = Dart(dart_host, dart_port, dart_api_version)
        self._action_handlers = {
            S3ActionTypes.copy.name: s3_copy
        }

    def run(self):
        action_context = self.dart.engine_action_checkout(os.environ.get('DART_ACTION_ID'))
        action = action_context.action

        state = ActionResultState.SUCCESS
        error_message = None
        try:
            _logger.info("*** S3Engine.run_action: %s", action.data.action_type_name)
            error_message = 'unsupported action: %s' % action.data.action_type_name
            assert action.data.action_type_name in self._action_handlers, error_message
            handler = self._action_handlers[action.data.action_type_name]
            handler(**action.data.args)
        except Exception as e:
            state = ActionResultState.FAILURE
            error_message = e.message + '\n\n\n' + traceback.format_exc()

        finally:
            self.dart.engine_action_checkin(action.id, ActionResult(state, error_message))


class S3EngineTaskRunner(Tool):
    def __init__(self):
        super(S3EngineTaskRunner, self).__init__(_logger, configure_app_context=False)

    def run(self):
        S3Engine(**(self.dart_config['engines']['s3_engine']['options'])).run()


if __name__ == '__main__':
    S3EngineTaskRunner().run()
