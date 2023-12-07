import base64

import pyzx as zx
from extraction.perceval import *
import perceval as pcvl
from qiskit import transpile, QuantumCircuit
import sys
import io
# import matplotlib
import json


# matplotlib.use('TkAgg')


def exit(data, warnings, errors):
    output = {"data": data, "warnings": warnings, "errors": errors}


if __name__ == '__main__':
    output = {"data": [], "warnings": [], "errors": []}
    data = []
    try:
        try:
            qasm = base64.b64decode(sys.argv[1]).decode()
        except IndexError:
            output["errors"].append("Empty argument. Valid QASM2.0 is needed")
            raise Exception("Exceptions")

        try:
            qc = QuantumCircuit.from_qasm_str(qasm)
            qc = transpile(qc, basis_gates=['cx', 'cz', 'rx', 'rz', 'h'])
        except Exception as e:
            output["errors"].append(f'Error parsing QASM input: {e.message}')
            raise Exception("Exceptions")

        g = zx.Circuit.from_qasm(qc.qasm()).to_graph()
        g.auto_detect_io()
        g.apply_state('0' * len(g.inputs()))
        p = PercevalExtraction(g.copy().to_json())

        graph_state = g.copy()
        to_graph_like(graph_state)
        graph_state.remove_vertices(graph_state.outputs())

        graph_state.normalize()
        plt = zx.draw_matplotlib(graph_state)
        f = io.BytesIO()
        plt.savefig(f, format="svg")
        output["data"].append({
            "name": "Resource State",
            "mime_type": "image/svg+xml",
            "value": base64.b64encode(f.getvalue()).decode()
        })

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

        if len(g.vertices()) > 20:
            output["warnings"].append(
                'MBQC scheme too large to print a photonic circuit')
            raise Exception("Warning")

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
    except Exception:
        pass
    finally:
        print(json.dumps(output))
