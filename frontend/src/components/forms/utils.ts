import Generation from "@shared/generation.type";

type TextExportOptions = {
    deletedQuestions?: boolean;
    deletedAnswers?: boolean;
    customQuestions?: boolean;
};

// convert quiz into text format
export const exportToText = (generation: Generation, options: TextExportOptions) => {
    const {
        deletedQuestions = false,
        deletedAnswers = false,
        customQuestions = false
    } = options;

    let questions = deletedQuestions
        ? generation.questions
        : generation.questions.filter((q) => !q.deleted);

    if (!customQuestions) {
        questions = questions.filter(q => !q.is_custom_question);
    }

    return questions
        .map(q => {
            const question = q.question;
            const answers = deletedAnswers
                ? q.answers
                : q.answers.filter(a => !a.deleted);

            const formatted = answers
                .filter(a => !a.deleted)
                .map(a => {
                    const letter = String.fromCharCode(97 + a.position);

                    return `    ${letter}: ${a.text}`
                })

            return `Question: ${question}\n${formatted.join("\n")}\n`;
    }).join("\n");
}
