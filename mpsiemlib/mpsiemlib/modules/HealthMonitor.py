from typing import List

from mpsiemlib.common import ModuleInterface, MPSIEMAuth, LoggingHandler, MPComponents, Settings
from mpsiemlib.common import exec_request


class HealthMonitor(ModuleInterface, LoggingHandler):
    """
    Health monitor module
    """

    __api_global_status = "/api/health_monitoring/v2/total_status"
    __api_checks = "/api/health_monitoring/v2/checks?limit={}&offset={}"
    __api_license_status = "/api/licensing/v2/license_validity"
    __api_agents_status = "/api/components/agent"
    __api_kb_status = "/api/v1/knowledgeBase"

    def __init__(self, auth: MPSIEMAuth, settings: Settings):
        ModuleInterface.__init__(self, auth, settings)
        LoggingHandler.__init__(self)
        self.__core_session = auth.connect(MPComponents.CORE)
        self.__core_hostname = auth.creds.core_hostname

    def get_health_status(self) -> str:
        """
        Получить общее состояние системы

        :return: "ok" - если нет ошибок
        """
        url = "https://{}{}".format(self.__core_hostname, self.__api_global_status)
        r = exec_request(self.__core_session,
                         url,
                         method='GET',
                         timeout=self.settings.connection_timeout)
        response = r.json()
        status = response.get("status")

        self.log.info('status=success, action=get_global_status, msg="Got global status", '
                      'hostname="{}" status="{}"'.format(self.__core_hostname, status))

        return status

    def get_health_errors(self) -> List[dict]:
        """
        Получить список ошибок из семафора.

        :return: Список ошибок или пустой массив, если ошибок нет
        """
        limit = 1000
        offset = 0
        api_url = self.__api_checks.format(limit, offset)
        url = "https://{}{}".format(self.__core_hostname, api_url)
        r = exec_request(self.__core_session,
                         url,
                         method='GET',
                         timeout=self.settings.connection_timeout)
        response = r.json()
        errors = response.get("items")

        self.log.info('status=success, action=get_errors, msg="Got errors", '
                      'hostname="{}" count="{}"'.format(self.__core_hostname, len(errors)))

        return errors

    def get_health_license_status(self) -> dict:
        """
        Получить статус лицензии.

        :return: dict
        """
        url = "https://{}{}".format(self.__core_hostname, self.__api_license_status)
        r = exec_request(self.__core_session,
                         url,
                         method='GET',
                         timeout=self.settings.connection_timeout)
        response = r.json()
        lic = response.get("license")
        status = {"valid": response.get("validity") == "valid",
                  "key": lic.get("keyNumber"),
                  "type": lic.get("licenseType"),
                  "granted": lic.get("keyDate"),
                  "expiration": lic.get("expirationDate"),
                  "assets": lic.get("assetsCount")}

        self.log.info('status=success, action=get_license_status, msg="Got license status", '
                      'hostname="{}"'.format(self.__core_hostname))

        return status

    def get_health_agents_status(self) -> List[dict]:
        """
        Получить статус агентов.

        :return: Список агентов и их параметры.
        """
        url = "https://{}{}".format(self.__core_hostname, self.__api_agents_status)
        r = exec_request(self.__core_session,
                         url,
                         method='GET',
                         timeout=self.settings.connection_timeout)
        response = r.json()

        agents = []
        for i in response:
            agents.append({
                "id": i.get("id"),
                "name": i.get("name"),
                "hostname": i.get("address"),
                "version": i.get("version"),
                "updates": i.get("availableUpdates"),
                "status": i.get("status"),
                "roles": i.get("roleNames"),
                "ip": i.get("ipAddresses"),
                "platform": i.get("platform"),
                "modules": i.get("modules")
            })

        self.log.info('status=success, action=get_license_status, msg="Got agents status", '
                      'hostname="{}" count="{}"'.format(self.__core_hostname, len(agents)))

        return agents

    def get_health_kb_status(self) -> dict:
        """
        Получить статус обновления VM контента в Core.

        :return: dict.
        """
        url = "https://{}{}".format(self.__core_hostname, self.__api_kb_status)
        r = exec_request(self.__core_session,
                         url,
                         method='GET',
                         timeout=self.settings.connection_timeout)
        response = r.json()
        local = response.get("localKnowledgeBase")
        remote = response.get("remoteKnowledgeBase")
        status = {"status": response.get("status"),
                  "local_updated": local.get("lastUpdate"),
                  "local_current_revision": local.get("localRevision"),
                  "local_global_revision": local.get("globalRevision"),
                  "kb_db_name": remote.get("name")}

        self.log.info('status=success, action=get_license_status, msg="Got license status", '
                      'hostname="{}"'.format(self.__core_hostname))

        return status

    def close(self):
        if self.__core_session is not None:
            self.__core_session.close()
