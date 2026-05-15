"""Tests do extrator de execution triggers (Universo 3 / Feature A)."""
from __future__ import annotations

from plugadvpl.parsing.triggers import extract_execution_triggers


def _kinds(triggers: list[dict]) -> list[str]:
    return [t["kind"] for t in triggers]


# --- Workflow ---------------------------------------------------------------


class TestWorkflowTrigger:
    def test_positive_twfprocess_with_callback(self) -> None:
        """TWFProcess + bReturn callback — extrai process_id + callback."""
        src = (
            'User Function WfSalNeg(cCli, nSld)\n'
            '   Local oWF := TWFProcess():New("SALNEG", "Saldo Negativo")\n'
            '   oWF:NewTask("Aviso", "/workflow/wf_salneg.htm")\n'
            '   oWF:cTo := "fin@x.com"\n'
            '   oWF:cSubject := "Saldo negativo"\n'
            '   oWF:bReturn := {|o| U_WfRetSN(o)}\n'
            '   oWF:Start()\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        wf = [t for t in triggers if t["kind"] == "workflow"]
        assert len(wf) >= 1
        # Primeiro trigger eh o TWFProcess.
        first = wf[0]
        assert first["metadata"]["process_id"] == "SALNEG"
        assert first["metadata"]["return_callback"].lower() == "u_wfretsn"
        assert first["metadata"]["template"] == "/workflow/wf_salneg.htm"
        assert first["metadata"]["to"] == "fin@x.com"
        assert first["metadata"]["is_legacy"] is False

    def test_positive_msworkflow_legacy(self) -> None:
        """MsWorkflow legado — emite trigger com is_legacy=True."""
        src = 'User Function ZOld()\n   MsWorkflow("OLD", "Legacy WF", oData)\nReturn\n'
        triggers = extract_execution_triggers(src)
        wf = [t for t in triggers if t["kind"] == "workflow"]
        assert any(t["metadata"].get("is_legacy") is True for t in wf)

    def test_positive_wfprepenv_callback(self) -> None:
        """WFPrepEnv em callback — emite trigger 'wf_callback'."""
        src = (
            'User Function WfRetSN(oProc)\n'
            '   WFPrepEnv("01", "0101")\n'
            '   // processa retorno\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        wf = [t for t in triggers if t["kind"] == "workflow"]
        assert any(t["target"] == "wf_callback" for t in wf)

    def test_negative_string_with_twfprocess(self) -> None:
        """TWFProcess em comentario nao deve disparar."""
        src = (
            'User Function ZOk()\n'
            '   // Antes era TWFProcess():New("X")\n'
            '   ConOut("nada")\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        assert "workflow" not in _kinds(triggers)

    def test_two_twfprocess_distinct_callbacks(self) -> None:
        """v0.4.3 (C1): 2 TWFProcess no mesmo arquivo nao devem misturar callbacks.

        Antes (bug): scope_end fixo de 5000 chars capturava callback do segundo
        TWFProcess e atribuia ao primeiro. Agora scope eh limitado pelo proximo
        TWFProcess (ou EOF se nao houver).
        """
        src = (
            'User Function W1()\n'
            '   oWF1 := TWFProcess():New("P1", "D1")\n'
            '   oWF1:bReturn := {|o| Cb1(o)}\n'
            'Return\n'
            'User Function W2()\n'
            '   oWF2 := TWFProcess():New("P2", "D2")\n'
            '   oWF2:bReturn := {|o| Cb2(o)}\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        wf = [t for t in triggers if t["kind"] == "workflow" and t["metadata"].get("process_id")]
        assert len(wf) == 2
        by_pid = {t["metadata"]["process_id"]: t for t in wf}
        assert by_pid["P1"]["metadata"]["return_callback"].lower() == "cb1"
        assert by_pid["P2"]["metadata"]["return_callback"].lower() == "cb2"


# --- Schedule ---------------------------------------------------------------


class TestScheduleTrigger:
    def test_positive_scheddef_report(self) -> None:
        """SchedDef retornando array tipo R — extrai pergunte + alias + titulo."""
        src = (
            'User Function FATR020()\n'
            '   // logica do relatorio\n'
            'Return\n'
            '\n'
            'Static Function SchedDef()\n'
            '   Local aParam := { "R", "FAT020", "SF2", {1,2}, "Faturamento por Periodo" }\n'
            'Return aParam\n'
        )
        triggers = extract_execution_triggers(src)
        sched = [t for t in triggers if t["kind"] == "schedule"]
        assert len(sched) == 1
        assert sched[0]["metadata"]["sched_type"] == "R"
        assert sched[0]["metadata"]["pergunte"] == "FAT020"
        assert sched[0]["metadata"]["alias"] == "SF2"
        assert sched[0]["metadata"]["ordens"] == [1, 2]
        assert "Faturamento" in sched[0]["metadata"]["titulo"]
        assert sched[0]["target"] == "FAT020"  # pergunte vira target

    def test_positive_scheddef_process(self) -> None:
        """SchedDef tipo P (Process)."""
        src = (
            'Static Function SchedDef()\n'
            '   Local a := { "P", "MGFINT", "", {1}, "Integracao Diaria" }\n'
            'Return a\n'
        )
        triggers = extract_execution_triggers(src)
        sched = [t for t in triggers if t["kind"] == "schedule"]
        assert len(sched) == 1
        assert sched[0]["metadata"]["sched_type"] == "P"

    def test_negative_function_named_schedxxx_not_scheddef(self) -> None:
        """`SchedHelper` etc nao deve disparar — so SchedDef exato."""
        src = (
            'Static Function SchedHelper()\n'
            '   Return Nil\n'
        )
        triggers = extract_execution_triggers(src)
        assert "schedule" not in _kinds(triggers)


# --- Job standalone --------------------------------------------------------


class TestJobStandaloneTrigger:
    def test_positive_main_function_with_rpcsetenv(self) -> None:
        """Main Function + RpcSetEnv + Sleep — daemon classico."""
        src = (
            'Main Function JobMonNFe()\n'
            '   RpcSetType(3)\n'
            '   RpcSetEnv("01","01",,,"FIS","JobMonNFe")\n'
            '   While !File("/stop_nfe.flg")\n'
            '      U_MonNFe()\n'
            '      Sleep(60000)\n'
            '   EndDo\n'
            '   RpcClearEnv()\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        jobs = [t for t in triggers if t["kind"] == "job_standalone"]
        assert len(jobs) == 1
        meta = jobs[0]["metadata"]
        assert meta["main_name"] == "JobMonNFe"
        assert meta["empresa"] == "01"
        assert meta["filial"] == "01"
        assert meta["modulo"] == "FIS"
        assert meta["sleep_seconds"] == 60
        assert meta["stop_flag"] == "/stop_nfe.flg"
        assert meta["no_license"] is True

    def test_rpcsetenv_six_literal_args_extracts_modulo(self) -> None:
        """v0.4.3 (C3): RpcSetEnv com 6 args literais consecutivos extrai modulo.

        Antes (bug): regex `(?:[^)]*?['\"](\\w*)['\"])?` consumia args 3 e 4
        sem alcancar o 5o. Agora usa split top-level pra pegar o 5o exato.
        """
        src = (
            'Main Function J()\n'
            '   RpcSetEnv("01","01","","","FAT","J")\n'
            '   While !File("/stop_j.flg")\n'
            '      Sleep(60000)\n'
            '   EndDo\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        jobs = [t for t in triggers if t["kind"] == "job_standalone"]
        assert len(jobs) == 1
        assert jobs[0]["metadata"]["empresa"] == "01"
        assert jobs[0]["metadata"]["filial"] == "01"
        assert jobs[0]["metadata"]["modulo"] == "FAT"

    def test_negative_main_function_without_rpcsetenv(self) -> None:
        """Main Function sem RpcSetEnv (entry point standalone) — NAO eh job."""
        src = (
            'Main Function MyExe()\n'
            '   ConOut("hello")\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        assert "job_standalone" not in _kinds(triggers)


# --- Mail send -------------------------------------------------------------


class TestMailSendTrigger:
    def test_positive_mailauto(self) -> None:
        """MailAuto direto — variante 'MailAuto'."""
        src = (
            'User Function ZAviso()\n'
            '   MailAuto("from@x.com", "to@y.com", "Aviso", "msg", {})\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        mails = [t for t in triggers if t["kind"] == "mail_send"]
        assert len(mails) == 1
        assert mails[0]["metadata"]["variant"] == "MailAuto"

    def test_positive_tmailmanager(self) -> None:
        """TMailManager + TMailMessage com anexo + MV_REL*."""
        src = (
            'User Function ZAnex()\n'
            '   Local oSrv := TMailManager():New()\n'
            '   Local oMsg := TMailMessage():New()\n'
            '   oSrv:Init("", SuperGetMv("MV_RELSERV"), SuperGetMv("MV_RELACNT"), "", 0, 587)\n'
            '   oMsg:AttachFile("relat.pdf")\n'
            '   oMsg:Send(oSrv)\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        mails = [t for t in triggers if t["kind"] == "mail_send"]
        assert len(mails) >= 1
        assert mails[0]["metadata"]["variant"] == "TMailManager"
        assert mails[0]["metadata"]["has_attachment"] is True
        assert mails[0]["metadata"]["uses_mv_rel"] is True

    def test_positive_udc_send_mail(self) -> None:
        """UDC `SEND MAIL ...` (MAILSEND.CH)."""
        src = (
            '#include "mailsend.ch"\n'
            'User Function ZUDC()\n'
            '   CONNECT SMTP SERVER cServer ACCOUNT cAcc PASSWORD cPwd RESULT lOk\n'
            '   SEND MAIL FROM cAcc TO cTo SUBJECT "X" BODY cMsg RESULT lOk\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        mails = [t for t in triggers if t["kind"] == "mail_send"]
        assert any(m["metadata"]["variant"] == "UDC" for m in mails)

    def test_positive_tmailmanager_solo_without_tmailmessage(self) -> None:
        """v0.4.3 (I1): TMailManager + :Send sem TMailMessage (legacy padrao).

        Antes: detector exigia TMailMessage; fontes legados (anteriores ao
        TMailMessage) eram ignorados. Agora TMailManager + :Send no mesmo
        scope tambem vira trigger.
        """
        src = (
            'User Function ZLegacy()\n'
            '   Local oSrv := TMailManager():New()\n'
            '   oSrv:Init("", SuperGetMv("MV_RELSERV"), SuperGetMv("MV_RELACNT"), "", 0, 587)\n'
            '   oSrv:SmtpConnect()\n'
            '   oSrv:SendMail(cFrom, aTo, cSubject, cBody)\n'
            '   oSrv:Disconnect()\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        mails = [t for t in triggers if t["kind"] == "mail_send"]
        assert len(mails) >= 1
        assert mails[0]["metadata"]["variant"] == "TMailManager"

    def test_negative_mail_in_comment(self) -> None:
        """MailAuto em comentario nao dispara."""
        src = (
            'User Function ZOk()\n'
            '   // MailAuto("...") foi removido\n'
            '   ConOut("ok")\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        assert "mail_send" not in _kinds(triggers)


# --- Multi-trigger ---------------------------------------------------------


class TestMultiTriggerSource:
    def test_job_with_mail_send(self) -> None:
        """Job daemon que envia email — 2 triggers no mesmo fonte."""
        src = (
            'Main Function JobAviso()\n'
            '   RpcSetEnv("01","01",,,"FAT","JobAviso")\n'
            '   While .T.\n'
            '      MailAuto("a@x", "b@y", "Aviso", "msg", {})\n'
            '      Sleep(3600000)\n'
            '   EndDo\n'
            'Return\n'
        )
        triggers = extract_execution_triggers(src)
        kinds = _kinds(triggers)
        assert "job_standalone" in kinds
        assert "mail_send" in kinds
        # Sleep(3600000) = 3600 segundos
        job = next(t for t in triggers if t["kind"] == "job_standalone")
        assert job["metadata"]["sleep_seconds"] == 3600
