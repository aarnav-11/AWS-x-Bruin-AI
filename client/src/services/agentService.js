import ApiService from './api';

export const agentService = {
  async tailorResume(resumeFile, jobDescription) {
    return ApiService.post('/agents/resume-tailor', {
      resume: resumeFile,
      job_description: jobDescription
    });
  },

  async coachInterview(jobDescription, experience) {
    return ApiService.post('/agents/interview-coach', {
      job_description: jobDescription,
      experience: experience
    });
  },

  async coachApplication(resumeFile, jobDescription) {
    return ApiService.post('/agents/application-coach', {
      resume: resumeFile,
      job_description: jobDescription
    });
  },

  async analyzeInstagram(profileUrl) {
    return ApiService.post('/agents/instagram-analyzer', {
      profile_url: profileUrl
    });
  },

  async analyzeWebsite(websiteUrl) {
    return ApiService.post('/agents/website-analyzer', {
      website_url: websiteUrl
    });
  },

  async summarizeContent(content) {
    return ApiService.post('/agents/summarizer', {
      content: content
    });
  }
};