import { ServiceError } from "@snek-at/function";

export class TaskNotFoundError extends ServiceError {
  constructor(id: string) {
    const message = `Task with ID '${id}' was not found. Please double-check the ID and try again.`;

    super(message, {
      statusCode: 404,
      code: "TASK_NOT_FOUND",
      message,
    });
  }
}

export class TaskCreationError extends ServiceError {
  constructor(message: string) {
    super(message, {
      statusCode: 500,
      code: "TASK_CREATION_ERROR",
      message,
    });
  }
}
