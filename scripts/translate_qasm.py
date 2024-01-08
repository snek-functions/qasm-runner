import base64

import pyzx as zx
from extraction.perceval import *
import perceval as pcvl
from qiskit import transpile, QuantumCircuit
import sys
import io
import matplotlib
import json


#matplotlib.use('TkAgg')

class QASMRunnerException(Exception):
    """Raised during parsing the QASM Input
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class QASMRunnerWarning(Warning):
    """Raised during parsing the QASM Input
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


def exit(data, warnings, errors):
    output = {"data": data, "warnings": warnings, "errors": errors}


if __name__ == '__main__':
    output = {"data": [], "warnings": [], "errors": []}
    data = []
    try:
        try:
            qasm = base64.b64decode(sys.argv[1]).decode()
        except IndexError:
            raise QASMRunnerException("Empty argument. Valid QASM2.0 is needed")

        try:
            qc = QuantumCircuit.from_qasm_str(qasm)
            qc = transpile(qc, basis_gates=['cx', 'cz', 'rx', 'rz', 'h'])
        except Exception as e:
            raise QASMRunnerException(f'Error parsing QASM input: {e.message}')

        try:
            g = zx.Circuit.from_qasm(qc.qasm()).to_graph()
            g.auto_detect_io()
            g.apply_state('0' * len(g.inputs()))
            p = PercevalExtraction(g.copy().to_json())
        except Exception as e:
            raise QASMRunnerException(f'Error translating QASM to ZX-graph: {e.message}')

        try:
            graph_state = g.copy()
            to_graph_like(graph_state)
            graph_state.remove_vertices(graph_state.outputs())
            for v in graph_state.vertices():
                graph_state.set_phase(v,0)

            graph_state.normalize()
            plt = zx.draw_matplotlib(graph_state)
            f = io.BytesIO()
            plt.savefig(f, format="svg")
            output["data"].append({
                "name": "Resource State",
                "mime_type": "image/svg+xml",
                "value": base64.b64encode(f.getvalue()).decode()
            })
        except AttributeError as e:
            raise QASMRunnerException(f'Error while extracting Resource state: {e}')
        except Exception as e:
            raise QASMRunnerException(f'Error while extracting Resource state: {e.message}')

        try:
            o_graph_state = p.graph.copy()
            o_graph_state.remove_vertices(o_graph_state.outputs())
            for v in o_graph_state.vertices():
                o_graph_state.set_phase(v,0)
            plt = zx.draw_matplotlib(o_graph_state)
            f = io.BytesIO()
            plt.savefig(f, format="svg")
            output["data"].append({
                "name": "Optimized Resource State",
                "mime_type": "image/svg+xml",
                "value": base64.b64encode(f.getvalue()).decode()
            })
        except Exception as e:
            raise QASMRunnerException(f'Error while extracting Optimized Resource State: {e.message}')

        try:
            zx_graph = p.graph.copy()

            zx_graph.normalize()
            plt = zx.draw_matplotlib(zx_graph)
            f = io.BytesIO()
            plt.savefig(f, format="svg")

            output["data"].append({
                "name": "Measurement Pattern",
                "mime_type": "image/svg+xml",
                "value": base64.b64encode(f.getvalue()).decode()
            })

            if len(g.vertices()) > 50:
                raise QASMRunnerWarning('MBQC has mor than 50 vertices and is too large to print a photonic circuit')
        except Exception as e:
            raise QASMRunnerException(f'Error while extracting Measurment Pattern: {e.message}')

        try:
            p.extract_clusters_from_graph_ghz_first()
            exp = p.create_setup(merge=True)
            pcvl.pdisplay_to_file(exp, path="test.svg",
                                  output_format=pcvl.Format.HTML)
            f = open("test.svg", "r")
            output["data"].append({
                "name": "Optical Circuit",
                "mime_type": "image/svg+xml",
                "value": base64.b64encode(f.read().encode()).decode()
            })
            f.close()
        except Exception as e:
            raise QASMRunnerException(f'Error while extracting Photonic Circuit: {e.message}')
    except QASMRunnerWarning as qasmW:
        output["warnings"].append(f'{qasmW.message}')
        pass
    except QASMRunnerException as qasme:
        output["errors"].append(f'{qasme.message}')
        pass
    finally:
#        with open("sample.json", "w") as outfile:
#           json.dump(output, outfile)
        print(json.dumps(output))
