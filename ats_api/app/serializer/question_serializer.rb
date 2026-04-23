class QuestionSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :title,
    :description,
    :details,
    :number_retakers,
    :time,
    :evaluation_id,
    :response_type,
    :position,
    :selective_process_id,
    :choices,
    :expected_response,
    :is_required,
    :parent_question_id,
    :value_father,
    :extra_params,
    :category,
    :competence_type,
    :framework,
    :bloom_level,
    :dreyfus_target,
    :framework_weights,
    :validation_type_weight,
    :wsi_reviewed,
    :wsi_metadata,
    :is_deleted,
    :created_at,
    :updated_at
  )

  attribute :ocean_trait do |object|
    Wsi::OceanTraitCanonical.to_api(object.ocean_trait)
  end
end
