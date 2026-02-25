#!/usr/bin/env python3
"""
SEPA-XML Generator
Generates ISO 20022 conformant SEPA XML files for German banks.

Supports:
- pain.001.001.09 (Customer Credit Transfer Initiation)
- pain.008.001.08 (Customer Direct Debit Initiation)
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
import re
import json


class SepaValidationError(Exception):
    """Raised when SEPA validation fails."""
    pass


def validate_iban(iban: str) -> bool:
    """Validate German IBAN format."""
    if not iban:
        raise SepaValidationError("IBAN is required")
    iban = iban.replace(" ", "").upper()
    if len(iban) != 22:
        raise SepaValidationError(f"German IBAN must be 22 characters, got {len(iban)}")
    if not iban.startswith("DE"):
        raise SepaValidationError(f"Only German IBANs supported, got {iban[:2]}")
    if not iban[2:].isdigit():
        raise SepaValidationError("IBAN must contain only digits after country code")
    return True


def validate_bic(bic: str) -> bool:
    """Validate BIC format."""
    if not bic:
        return True  # BIC optional for some banks
    bic = bic.replace(" ", "").upper()
    if len(bic) not in [8, 11]:
        raise SepaValidationError(f"BIC must be 8 or 11 characters, got {len(bic)}")
    if not re.match(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$', bic):
        raise SepaValidationError(f"Invalid BIC format: {bic}")
    return True


def validate_amount(amount: float) -> bool:
    """Validate amount constraints."""
    if amount <= 0:
        raise SepaValidationError("Amount must be positive")
    if amount > 999999999.99:
        raise SepaValidationError("Amount exceeds maximum of 999,999,999.99 EUR")
    return True


def format_amount(amount: float) -> str:
    """Format amount to SEPA decimal format."""
    d = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return str(d)


def sanitize_text(text: str, max_length: int) -> str:
    """Sanitize text for SEPA XML."""
    if not text:
        return ""
    # Replace XML special chars with +
    for char in ["\u003c", "\u003e", "\u0026"]:
        text = text.replace(char, "+")
    # Limit length
    return text[:max_length].strip()


class SepaCreditTransfer:
    """Generator for SEPA Credit Transfer (pain.001.001.09)."""
    
    NS = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"
    
    def __init__(self, msg_id: str, initiator_name: str, creation_date_time: Optional[str] = None):
        self.msg_id = sanitize_text(msg_id, 35)
        self.initiator_name = sanitize_text(initiator_name, 140)
        self.creation_date_time = creation_date_time or datetime.now().isoformat()
        self.payment_infos: List[dict] = []
        self.transactions: List[dict] = []
        
    def add_payment_info(
        self,
        payment_info_id: str,
        debtor_name: str,
        debtor_iban: str,
        debtor_bic: Optional[str] = None,
        requested_execution_date: Optional[str] = None
    ) -> None:
        """Add payment information block."""
        validate_iban(debtor_iban)
        if debtor_bic:
            validate_bic(debtor_bic)
            
        self.payment_infos.append({
            "id": sanitize_text(payment_info_id, 35),
            "debtor_name": sanitize_text(debtor_name, 140),
            "debtor_iban": debtor_iban.replace(" ", "").upper(),
            "debtor_bic": debtor_bic.replace(" ", "").upper() if debtor_bic else None,
            "requested_execution_date": requested_execution_date or datetime.now().strftime("%Y-%m-%d")
        })
        
    def add_transaction(
        self,
        end_to_end_id: str,
        amount: float,
        creditor_name: str,
        creditor_iban: str,
        creditor_bic: Optional[str] = None,
        remittance_info: Optional[str] = None,
        payment_info_index: int = 0
    ) -> None:
        """Add a credit transfer transaction."""
        validate_amount(amount)
        validate_iban(creditor_iban)
        if creditor_bic:
            validate_bic(creditor_bic)
            
        self.transactions.append({
            "end_to_end_id": sanitize_text(end_to_end_id, 35),
            "amount": amount,
            "creditor_name": sanitize_text(creditor_name, 140),
            "creditor_iban": creditor_iban.replace(" ", "").upper(),
            "creditor_bic": creditor_bic.replace(" ", "").upper() if creditor_bic else None,
            "remittance_info": sanitize_text(remittance_info, 140),
            "payment_info_index": payment_info_index
        })
        
    def to_xml(self) -> str:
        """Generate SEPA XML string."""
        if not self.payment_infos:
            raise SepaValidationError("At least one payment info required")
        if not self.transactions:
            raise SepaValidationError("At least one transaction required")
            
        # Register namespace
        ET.register_namespace('', self.NS)
        
        # Root element
        root = ET.Element(f"{{{self.NS}}}Document")
        ccti = ET.SubElement(root, f"{{{self.NS}}}CstmrCdtTrfInitn")
        
        # Group Header
        grp_hdr = ET.SubElement(ccti, f"{{{self.NS}}}GrpHdr")
        ET.SubElement(grp_hdr, f"{{{self.NS}}}MsgId").text = self.msg_id
        ET.SubElement(grp_hdr, f"{{{self.NS}}}CreDtTm").text = self.creation_date_time
        ET.SubElement(grp_hdr, f"{{{self.NS}}}NbOfTxs").text = str(len(self.transactions))
        
        ctrl_sum = sum(t["amount"] for t in self.transactions)
        ET.SubElement(grp_hdr, f"{{{self.NS}}}CtrlSum").text = format_amount(ctrl_sum)
        
        initg_pty = ET.SubElement(grp_hdr, f"{{{self.NS}}}InitgPty")
        ET.SubElement(initg_pty, f"{{{self.NS}}}Nm").text = self.initiator_name
        
        # Payment Information Blocks
        for pmt_info in self.payment_infos:
            pmt_inf = ET.SubElement(ccti, f"{{{self.NS}}}PmtInf")
            ET.SubElement(pmt_inf, f"{{{self.NS}}}PmtInfId").text = pmt_info["id"]
            ET.SubElement(pmt_inf, f"{{{self.NS}}}PmtMtd").text = "TRF"
            ET.SubElement(pmt_inf, f"{{{self.NS}}}NbOfTxs").text = str(
                sum(1 for t in self.transactions if t["payment_info_index"] == self.payment_infos.index(pmt_info))
            )
            
            pmt_inf_ctrl_sum = sum(
                t["amount"] for t in self.transactions 
                if t["payment_info_index"] == self.payment_infos.index(pmt_info)
            )
            ET.SubElement(pmt_inf, f"{{{self.NS}}}CtrlSum").text = format_amount(pmt_inf_ctrl_sum)
            
            pmt_tp_inf = ET.SubElement(pmt_inf, f"{{{self.NS}}}PmtTpInf")
            svc_lvl = ET.SubElement(pmt_tp_inf, f"{{{self.NS}}}SvcLvl")
            ET.SubElement(svc_lvl, f"{{{self.NS}}}Cd").text = "SEPA"
            
            ET.SubElement(pmt_inf, f"{{{self.NS}}}ReqdExctnDt").text = pmt_info["requested_execution_date"]
            
            dbtr = ET.SubElement(pmt_inf, f"{{{self.NS}}}Dbtr")
            ET.SubElement(dbtr, f"{{{self.NS}}}Nm").text = pmt_info["debtor_name"]
            
            dbtr_acct = ET.SubElement(pmt_inf, f"{{{self.NS}}}DbtrAcct")
            id_elem = ET.SubElement(dbtr_acct, f"{{{self.NS}}}Id")
            ET.SubElement(id_elem, f"{{{self.NS}}}IBAN").text = pmt_info["debtor_iban"]
            
            if pmt_info["debtor_bic"]:
                dbtr_agt = ET.SubElement(pmt_inf, f"{{{self.NS}}}DbtrAgt")
                fin_instn_id = ET.SubElement(dbtr_agt, f"{{{self.NS}}}FinInstnId")
                ET.SubElement(fin_instn_id, f"{{{self.NS}}}BICFI").text = pmt_info["debtor_bic"]
            
            # Credit Transfer Transaction Information
            for trx in self.transactions:
                if trx["payment_info_index"] != self.payment_infos.index(pmt_info):
                    continue
                    
                cdt_trf_tx_inf = ET.SubElement(pmt_inf, f"{{{self.NS}}}CdtTrfTxInf")
                
                pmt_id = ET.SubElement(cdt_trf_tx_inf, f"{{{self.NS}}}PmtId")
                ET.SubElement(pmt_id, f"{{{self.NS}}}EndToEndId").text = trx["end_to_end_id"]
                
                amt = ET.SubElement(cdt_trf_tx_inf, f"{{{self.NS}}}Amt")
                instd_amt = ET.SubElement(amt, f"{{{self.NS}}}InstdAmt", {"Ccy": "EUR"})
                instd_amt.text = format_amount(trx["amount"])
                
                cdtr_agt = ET.SubElement(cdt_trf_tx_inf, f"{{{self.NS}}}CdtrAgt")
                fin_instn_id = ET.SubElement(cdtr_agt, f"{{{self.NS}}}FinInstnId")
                if trx["creditor_bic"]:
                    ET.SubElement(fin_instn_id, f"{{{self.NS}}}BICFI").text = trx["creditor_bic"]
                else:
                    ET.SubElement(fin_instn_id, f"{{{self.NS}}}Othr").text = "NOTPROVIDED"
                
                cdtr = ET.SubElement(cdt_trf_tx_inf, f"{{{self.NS}}}Cdtr")
                ET.SubElement(cdtr, f"{{{self.NS}}}Nm").text = trx["creditor_name"]
                
                cdtr_acct = ET.SubElement(cdt_trf_tx_inf, f"{{{self.NS}}}CdtrAcct")
                id_elem = ET.SubElement(cdtr_acct, f"{{{self.NS}}}Id")
                ET.SubElement(id_elem, f"{{{self.NS}}}IBAN").text = trx["creditor_iban"]
                
                if trx["remittance_info"]:
                    rmt_inf = ET.SubElement(cdt_trf_tx_inf, f"{{{self.NS}}}RmtInf")
                    ET.SubElement(rmt_inf, f"{{{self.NS}}}Ustrd").text = trx["remittance_info"]
        
        # Pretty print XML
        return self._prettify(root)
    
    def _prettify(self, elem: ET.Element, level: int = 0) -> str:
        """Return pretty-printed XML string."""
        indent = "  "
        i = "\n" + level * indent
        
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._prettify(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
                
        return ET.tostring(elem, encoding='unicode', xml_declaration=True)
    
    def to_file(self, path: str) -> None:
        """Write XML to file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_xml())
            
    def validate(self) -> bool:
        """Validate the SEPA document."""
        try:
            self.to_xml()
            return True
        except SepaValidationError:
            return False


class SepaDirectDebit:
    """Generator for SEPA Direct Debit (pain.008.001.08)."""
    
    NS = "urn:iso:std:iso:20022:tech:xsd:pain.008.001.08"
    SEQUENCE_TYPES = ["FRST", "RCUR", "FNAL", "OOFF"]
    
    def __init__(
        self,
        msg_id: str,
        initiator_name: str,
        creation_date_time: Optional[str] = None,
        sequence_type: str = "RCUR"
    ):
        if sequence_type not in self.SEQUENCE_TYPES:
            raise SepaValidationError(f"Invalid sequence type: {sequence_type}")
            
        self.msg_id = sanitize_text(msg_id, 35)
        self.initiator_name = sanitize_text(initiator_name, 140)
        self.creation_date_time = creation_date_time or datetime.now().isoformat()
        self.sequence_type = sequence_type
        self.payment_infos: List[dict] = []
        self.transactions: List[dict] = []
        
    def add_payment_info(
        self,
        payment_info_id: str,
        creditor_name: str,
        creditor_iban: str,
        creditor_id: str,
        creditor_bic: Optional[str] = None,
        requested_collection_date: Optional[str] = None
    ) -> None:
        """Add payment information block."""
        validate_iban(creditor_iban)
        if creditor_bic:
            validate_bic(creditor_bic)
            
        self.payment_infos.append({
            "id": sanitize_text(payment_info_id, 35),
            "creditor_name": sanitize_text(creditor_name, 140),
            "creditor_iban": creditor_iban.replace(" ", "").upper(),
            "creditor_id": sanitize_text(creditor_id, 35),
            "creditor_bic": creditor_bic.replace(" ", "").upper() if creditor_bic else None,
            "requested_collection_date": requested_collection_date or datetime.now().strftime("%Y-%m-%d")
        })
        
    def add_transaction(
        self,
        end_to_end_id: str,
        amount: float,
        debtor_name: str,
        debtor_iban: str,
        mandate_id: str,
        mandate_signing_date: str,
        debtor_bic: Optional[str] = None,
        remittance_info: Optional[str] = None,
        payment_info_index: int = 0
    ) -> None:
        """Add a direct debit transaction."""
        validate_amount(amount)
        validate_iban(debtor_iban)
        if debtor_bic:
            validate_bic(debtor_bic)
            
        self.transactions.append({
            "end_to_end_id": sanitize_text(end_to_end_id, 35),
            "amount": amount,
            "debtor_name": sanitize_text(debtor_name, 140),
            "debtor_iban": debtor_iban.replace(" ", "").upper(),
            "debtor_bic": debtor_bic.replace(" ", "").upper() if debtor_bic else None,
            "mandate_id": sanitize_text(mandate_id, 35),
            "mandate_signing_date": mandate_signing_date,
            "remittance_info": sanitize_text(remittance_info, 140),
            "payment_info_index": payment_info_index
        })
        
    def to_xml(self) -> str:
        """Generate SEPA Direct Debit XML string."""
        if not self.payment_infos:
            raise SepaValidationError("At least one payment info required")
        if not self.transactions:
            raise SepaValidationError("At least one transaction required")
            
        ET.register_namespace('', self.NS)
        
        root = ET.Element(f"{{{self.NS}}}Document")
        drct_dbt_initn = ET.SubElement(root, f"{{{self.NS}}}CstmrDrctDbtInitn")
        
        # Group Header
        grp_hdr = ET.SubElement(drct_dbt_initn, f"{{{self.NS}}}GrpHdr")
        ET.SubElement(grp_hdr, f"{{{self.NS}}}MsgId").text = self.msg_id
        ET.SubElement(grp_hdr, f"{{{self.NS}}}CreDtTm").text = self.creation_date_time
        ET.SubElement(grp_hdr, f"{{{self.NS}}}NbOfTxs").text = str(len(self.transactions))
        
        ctrl_sum = sum(t["amount"] for t in self.transactions)
        ET.SubElement(grp_hdr, f"{{{self.NS}}}CtrlSum").text = format_amount(ctrl_sum)
        
        initg_pty = ET.SubElement(grp_hdr, f"{{{self.NS}}}InitgPty")
        ET.SubElement(initg_pty, f"{{{self.NS}}}Nm").text = self.initiator_name
        
        # Payment Information
        for pmt_info in self.payment_infos:
            pmt_inf = ET.SubElement(drct_dbt_initn, f"{{{self.NS}}}PmtInf")
            ET.SubElement(pmt_inf, f"{{{self.NS}}}PmtInfId").text = pmt_info["id"]
            ET.SubElement(pmt_inf, f"{{{self.NS}}}PmtMtd").text = "DD"
            ET.SubElement(pmt_inf, f"{{{self.NS}}}NbOfTxs").text = str(
                sum(1 for t in self.transactions if t["payment_info_index"] == self.payment_infos.index(pmt_info))
            )
            
            pmt_inf_ctrl_sum = sum(
                t["amount"] for t in self.transactions
                if t["payment_info_index"] == self.payment_infos.index(pmt_info)
            )
            ET.SubElement(pmt_inf, f"{{{self.NS}}}CtrlSum").text = format_amount(pmt_inf_ctrl_sum)
            
            pmt_tp_inf = ET.SubElement(pmt_inf, f"{{{self.NS}}}PmtTpInf")
            svc_lvl = ET.SubElement(pmt_tp_inf, f"{{{self.NS}}}SvcLvl")
            ET.SubElement(svc_lvl, f"{{{self.NS}}}Cd").text = "SEPA"
            lcl_instrm = ET.SubElement(pmt_tp_inf, f"{{{self.NS}}}LclInstrm")
            ET.SubElement(lcl_instrm, f"{{{self.NS}}}Cd").text = "CORE"
            seq_tp = ET.SubElement(pmt_tp_inf, f"{{{self.NS}}}SeqTp")
            ET.SubElement(seq_tp, f"{{{self.NS}}}Cd").text = self.sequence_type
            
            ET.SubElement(pmt_inf, f"{{{self.NS}}}ReqdColltnDt").text = pmt_info["requested_collection_date"]
            
            cdtr = ET.SubElement(pmt_inf, f"{{{self.NS}}}Cdtr")
            ET.SubElement(cdtr, f"{{{self.NS}}}Nm").text = pmt_info["creditor_name"]
            
            cdtr_acct = ET.SubElement(pmt_inf, f"{{{self.NS}}}CdtrAcct")
            id_elem = ET.SubElement(cdtr_acct, f"{{{self.NS}}}Id")
            ET.SubElement(id_elem, f"{{{self.NS}}}IBAN").text = pmt_info["creditor_iban"]
            
            cdtr_agt = ET.SubElement(pmt_inf, f"{{{self.NS}}}CdtrAgt")
            fin_instn_id = ET.SubElement(cdtr_agt, f"{{{self.NS}}}FinInstnId")
            if pmt_info["creditor_bic"]:
                ET.SubElement(fin_instn_id, f"{{{self.NS}}}BICFI").text = pmt_info["creditor_bic"]
            else:
                othr = ET.SubElement(fin_instn_id, f"{{{self.NS}}}Othr")
                ET.SubElement(othr, f"{{{self.NS}}}Id").text = "NOTPROVIDED"
            
            cdtr_schme_id = ET.SubElement(pmt_inf, f"{{{self.NS}}}CdtrSchmeId")
            id_elem = ET.SubElement(cdtr_schme_id, f"{{{self.NS}}}Id")
            prvt_id = ET.SubElement(id_elem, f"{{{self.NS}}}PrvtId")
            othr = ET.SubElement(prvt_id, f"{{{self.NS}}}Othr")
            ET.SubElement(othr, f"{{{self.NS}}}Id").text = pmt_info["creditor_id"]
            schme_nm = ET.SubElement(othr, f"{{{self.NS}}}SchmeNm")
            ET.SubElement(schme_nm, f"{{{self.NS}}}Prtry").text = "SEPA"
            
            # Direct Debit Transaction Information
            for trx in self.transactions:
                if trx["payment_info_index"] != self.payment_infos.index(pmt_info):
                    continue
                    
                drct_dbt_tx_inf = ET.SubElement(pmt_inf, f"{{{self.NS}}}DrctDbtTxInf")
                
                pmt_id = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}PmtId")
                ET.SubElement(pmt_id, f"{{{self.NS}}}EndToEndId").text = trx["end_to_end_id"]
                
                amt = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}Amt")
                instd_amt = ET.SubElement(amt, f"{{{self.NS}}}InstdAmt", {"Ccy": "EUR"})
                instd_amt.text = format_amount(trx["amount"])
                
                drct_dbt_tx = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}DrctDbtTx")
                mndt_rltd_inf = ET.SubElement(drct_dbt_tx, f"{{{self.NS}}}MndtRltdInf")
                ET.SubElement(mndt_rltd_inf, f"{{{self.NS}}}MndtId").text = trx["mandate_id"]
                dt_of_sgntr = ET.SubElement(mndt_rltd_inf, f"{{{self.NS}}}DtOfSgntr")
                dt_of_sgntr.text = trx["mandate_signing_date"]
                
                dbtr_agt = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}DbtrAgt")
                fin_instn_id = ET.SubElement(dbtr_agt, f"{{{self.NS}}}FinInstnId")
                if trx["debtor_bic"]:
                    ET.SubElement(fin_instn_id, f"{{{self.NS}}}BICFI").text = trx["debtor_bic"]
                else:
                    othr = ET.SubElement(fin_instn_id, f"{{{self.NS}}}Othr")
                    ET.SubElement(othr, f"{{{self.NS}}}Id").text = "NOTPROVIDED"
                
                dbtr = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}Dbtr")
                ET.SubElement(dbtr, f"{{{self.NS}}}Nm").text = trx["debtor_name"]
                
                dbtr_acct = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}DbtrAcct")
                id_elem = ET.SubElement(dbtr_acct, f"{{{self.NS}}}Id")
                ET.SubElement(id_elem, f"{{{self.NS}}}IBAN").text = trx["debtor_iban"]
                
                if trx["remittance_info"]:
                    rmt_inf = ET.SubElement(drct_dbt_tx_inf, f"{{{self.NS}}}RmtInf")
                    ET.SubElement(rmt_inf, f"{{{self.NS}}}Ustrd").text = trx["remittance_info"]
        
        return self._prettify(root)
    
    def _prettify(self, elem: ET.Element, level: int = 0) -> str:
        """Return pretty-printed XML string."""
        indent = "  "
        i = "\n" + level * indent
        
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._prettify(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
                
        return ET.tostring(elem, encoding='unicode', xml_declaration=True)
    
    def to_file(self, path: str) -> None:
        """Write XML to file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_xml())
            
    def validate(self) -> bool:
        """Validate the SEPA document."""
        try:
            self.to_xml()
            return True
        except SepaValidationError:
            return False


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SEPA XML Generator")
    parser.add_argument("--input", "-i", help="Input JSON file")
    parser.add_argument("--output", "-o", help="Output XML file")
    parser.add_argument("--type", "-t", choices=["credit-transfer", "direct-debit"],
                       default="credit-transfer", help="SEPA message type")
    parser.add_argument("--validate", "-v", help="Validate existing XML file")
    
    args = parser.parse_args()
    
    if args.validate:
        try:
            with open(args.validate, 'r', encoding='utf-8') as f:
                content = f.read()
            ET.fromstring(content)
            print(f"✅ {args.validate} is valid XML")
            return 0
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return 1
    
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if args.type == "credit-transfer":
            gen = SepaCreditTransfer(
                msg_id=data["msg_id"],
                initiator_name=data["initiator_name"],
                creation_date_time=data.get("creation_date_time")
            )
            for pmt in data.get("payment_infos", []):
                gen.add_payment_info(**pmt)
            for trx in data.get("transactions", []):
                gen.add_transaction(**trx)
        else:
            gen = SepaDirectDebit(
                msg_id=data["msg_id"],
                initiator_name=data["initiator_name"],
                creation_date_time=data.get("creation_date_time"),
                sequence_type=data.get("sequence_type", "RCUR")
            )
            for pmt in data.get("payment_infos", []):
                gen.add_payment_info(**pmt)
            for trx in data.get("transactions", []):
                gen.add_transaction(**trx)
        
        xml_output = gen.to_xml()
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(xml_output)
            print(f"✅ Generated {args.output}")
        else:
            print(xml_output)
        
        return 0
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    exit(main())
