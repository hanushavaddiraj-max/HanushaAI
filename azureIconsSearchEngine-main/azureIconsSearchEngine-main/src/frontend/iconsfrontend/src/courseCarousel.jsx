import React from "react";
import "./courseCarousel.css";
import UdemyCourseComponent from "./udemyCourseComponent";

export default function CourseCarousel() {
    const courses = [
        {
            imageUrl: "https://azureiconskuljot.blob.core.windows.net/iconsofazure/All_Things_RAG.png",
            courseTitle: "RAG with Azure OpenAI (Azure AI Search, CosmosDB, GraphRAG and more)",
            courseLink: "https://www.udemy.com/course/rag-with-azure-openai-ai-search-cosmosdb-graphrag-more/?referralCode=4DF77685B7D27902AA0C"

        },
        {
            imageUrl: "https://azureiconskuljot.blob.core.windows.net/iconsofazure/Ai_and_security.png",
            courseTitle: "AI and Cloud Security (Microsoft Azure)",
            courseLink: "https://www.udemy.com/course/securing-ai-with-microsoft-cloud/?referralCode=B14E09815F652231BBE1"
        },
        {
            imageUrl: "https://azureiconskuljot.blob.core.windows.net/iconsofazure/Copilot World! (3).png",
            courseTitle: "Microsoft Copilot World",
            courseLink: "https://www.udemy.com/course/copilot-world-complete-deep-dive/?referralCode=F077037493AABB4DFC17"
        },
        {
            imageUrl: "https://azureiconskuljot.blob.core.windows.net/iconsofazure/azure_openai_logo.png",
            courseTitle: "Azure Generative (OpenAI) + Predictive AI (23+ Hours)",
            courseLink: "https://www.udemy.com/course/mastering-azure-openai-from-zero-to-hero/?referralCode=11311E20568531B8494B"
        },
        {
            imageUrl: "https://azureiconskuljot.blob.core.windows.net/iconsofazure/Azure AI Studio (5).png",
            courseTitle: "Master Azure AI Studio: Prompt Flow, LLMOps & RAG",
            courseLink: "https://www.udemy.com/course/master-azure-ai-studio-prompt-flow-llmops-rag/?referralCode=960443FE0F0DB79CB839"
        }
    ]
    return (
        <div className="parentDiv">
            <div className="h1">
                <h1>Check out my Udemy Courses</h1>
            </div>
            <div className="carouselDiv">
             {courses.map((course) => (
                 <UdemyCourseComponent key={course.courseTitle} imageUrl={course.imageUrl} courseTitle={course.courseTitle} courseLink={course.courseLink}/>
             ))}
            </div>
            
        </div>
    )
}
