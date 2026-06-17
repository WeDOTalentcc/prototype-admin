class ApplicationRecord < ActiveRecord::Base
  include AccountScopable
  primary_abstract_class
end
