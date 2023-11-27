import { defineService, logger } from "@cronitio/pylon";

import Translator from "./services/translator.service";
import { TaskCreationError } from "./errors/translator.errors";

const translationQueue = new Translator();

export default defineService({
  Query: {
    translate: async (taskId: string) => {
      return await translationQueue.get(taskId);
    },
  },
  Mutation: {
    translate: async (base64Code: string) => {
      try {
        return await translationQueue.translate(base64Code);
      } catch (error) {
        throw new TaskCreationError(error);
      }
    },
  },
});
