class SetEvaluationIsChatbotTrueAsDefault < ActiveRecord::Migration[7.1]
  def change
    change_column_default :evaluations, :is_chatbot, true
    change_column_default :evaluations, :ai_enabled, true
  end
end
