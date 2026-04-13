# frozen_string_literal: true

module V1
  module Users
    class CandidatesController < ApplicationController
      include ResourceLoader

      def index
        perform_search(
          model: Candidate,
          serializer: CandidateSerializer
        )
      end

      def show
        render_success(@candidate, serializer: CandidateSerializer)
      end

      def create
        @candidate = Candidate.new(candidate_params)

        if @candidate.save
          return render_success(@candidate, serializer: CandidateSerializer, status: :created)
        end
        render_error(@candidate, status: :unprocessable_entity)
      end

      def update
        @candidate.update(candidate_params) ? render_success(@candidate, serializer: CandidateSerializer) : render_error(@candidate)
      end

      def destroy
        @candidate.destroy
        render_no_content
      end

      private

      def candidate_params
        params.require(:candidate).permit(
          :name, :surname, :email, :secondary_email, :mobile_phone, :phone, :secondary_phone, :linkedin, :github,
          :portfolio, :current_company, :role_name, :position_level, :self_introduction, :curriculum_text, :date_birth,
          :gender, :nationality, :marital_status, :cpf, :street, :number, :district, :zip, :city, :state, :country, :complement,
          :clt_expectation, :pj_expectation, :freelance_expectation, :current_salary, :desired_salary, :currency, :remote_work,
          :mobility, :interests, :comments, :source, :avatar_url, :curriculum_pdf_url, :completed_register, :account_id, :accept_terms,
          :diversity_race_ethnicity, :diversity_disability, :diversity_disability_type,
          :diversity_lgbtqia, :diversity_refugee, :diversity_age_50_plus, :diversity_indigenous,
          :diversity_self_declared_at, :diversity_document_deadline,
          :seniority_level, :years_of_experience, :fork_uuid,
          diversity_documents: {}, languages: [],
          technical_skills: [], soft_skills: [], certifications: []
        )
      end
    end
  end
end
