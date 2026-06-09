# Maps fault codes to Korean maintenance action text from the fault code database
from typing import Optional
from models.diagnosis_result import VoltageState
from csc_04_fault_code_generator.csu_01_fault_code_mapper import FaultCodeMapper

_NO_FAULT_MSG = "정상 상태입니다. 정기 점검 일정에 따라 유지보수를 진행하세요."
_NO_DATA_MSG  = "센서 데이터 없음. 전압 센서 연결 및 케이블 상태를 확인하세요."
_SENSOR_ERR_MSG = "센서 오류 감지. 센서 배선, 전원, 펌웨어 상태를 점검하세요."
_RAPID_DROP_MSG = "급격한 전압 강하 감지. 배터리 상태 및 전원 계통 즉시 점검 후 착륙하세요."


class MaintenanceActionMapper:
    def __init__(self, fault_mapper: Optional[FaultCodeMapper] = None):
        self._mapper = fault_mapper or FaultCodeMapper()

    def get_action(self, fault_code: Optional[str], state: Optional[VoltageState] = None) -> str:
        if fault_code:
            fc = self._mapper.get_fault_code_obj(fault_code)
            if fc:
                return fc.maintenance_ko

        if state == VoltageState.NO_DATA:
            return _NO_DATA_MSG
        if state == VoltageState.SENSOR_ERROR:
            return _SENSOR_ERR_MSG
        if state == VoltageState.RAPID_DROP:
            return _RAPID_DROP_MSG
        if state == VoltageState.NORMAL:
            return _NO_FAULT_MSG

        return "해당 고장 코드에 대한 정비 절차를 매뉴얼에서 확인하세요."

    def get_description(self, fault_code: str) -> str:
        fc = self._mapper.get_fault_code_obj(fault_code)
        return fc.description_ko if fc else ""
