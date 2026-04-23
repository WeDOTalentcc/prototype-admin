class AddAgentSearchCriteriaToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :agent_search_criteria, :text
  end
end
