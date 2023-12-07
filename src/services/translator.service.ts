import Queue, { Job } from "bull";
import util from "util";
const exec = util.promisify((await import("child_process")).exec);

import { TaskNotFoundError } from "../errors/translator.errors";

type JobData = {
  base64Qasm: string;
  result?: {
    errors: string[];
    warnings: string[];
    translation: Array<{
      mimeType: string;
      value: string;
      dataUri: string;
      name?: string;
    }>;
  };
};

type Q = Queue.Queue<JobData>;

class Translator {
  private queue: Q;

  constructor() {
    this.queue = new Queue(
      "translation",
      process.env.REDIS_URL || "redis://localhost:6379"
    );

    this.queue.process(async (job) => {
      const base64Qasm = job.data.base64Qasm;
      // Simulating translation by decoding base64 and queuing the result as SVG list
      // Simulating actual translation service by mocking it
      return new Promise<void>((resolve) => {
        setTimeout(async () => {
          // Mocked translation service. Replace it with the actual implementation later
          const translation = await this.translateQASM(base64Qasm);
          job.update({
            ...job.data,
            ...translation,
          }); // Update the job with the translated SVG list
          resolve();
        }, 5000);
      });
    });
  }

  private async jobToTask(job: Job<JobData>) {
    return {
      id: job.id.toString(),
      status: () => job.getState(),
      progress: () => job.data,
      data: job.data,
    };
  }

  public async translate(base64Qasm: string) {
    const job = await this.queue.add({ base64Qasm });

    return this.jobToTask(job);
  }

  public async get(id: string) {
    const job = await this.queue.getJob(id);

    if (!job) {
      throw new TaskNotFoundError("Job not found");
    }

    return this.jobToTask(job);
  }

  private async translateQASM(base64Qasm: string) {
    // Run ./scripts/translate_qasm.py

    const { stdout, stderr } = await exec(
      `python3 ./scripts/translate_qasm.py ${base64Qasm}`
    );

    if (stderr) {
      throw new Error(stderr);
    }

    const result = JSON.parse(stdout) as {
      errors: string[];
      warnings: string[];
      data: {
        name: string;
        mime_type: string;
        value: string;
      }[];
    };

    const translation = result.data.map((data) => ({
      mimeType: data.mime_type,
      value: data.value,
      dataUri: `data:${data.mime_type};base64,${data.value}`,
      name: data.name,
    }));

    return {
      errors: result.errors,
      warnings: result.warnings,
      translation,
    };
  }
}

export default Translator;
